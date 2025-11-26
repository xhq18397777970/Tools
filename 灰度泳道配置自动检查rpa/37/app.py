#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import json
import traceback
import logging
from logging.handlers import RotatingFileHandler
from modify_checker import (
    check_nodegroup_connectivity,
    run_salt_command_config,
    merge_json_strings_config,
    analyze_salt_results_config,
    run_salt_command_log,
    merge_json_strings_log,
    analyze_log_data_log,
    check_gray_route_logs_log,
    config_file_exist,
    log_file_exist
)
from delete_checker import (
    run_delete_salt,
    merge_delete_json,
    analyze_delete_results,
)
from auth import validate_auth_params  # 导入鉴权函数

app = Flask(__name__)

# 配置日志
def setup_logger():
    # 创建日志记录器
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # 设置最低日志级别

    # 创建文件处理器，设置日志文件最大10MB，保留3个备份
    file_handler = RotatingFileHandler(
        'app.log', maxBytes=10*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别

    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

@app.route('/check', methods=['POST'])
def execute_check():
    """
    执行检查的主接口
    接收JSON格式的请求体，例如:
    {
        "gray_domain": "color.7fresh.com",
        "gray_swim_lane": "GRAY_RETAIL_MAIN",
        "gray_ups": "gray_retail_main",
        "Auth": "xxxxxx",
        "Timestamp": 1234567890,
        "User": "api_np"
    }
    """
    try:
        logger.info("【开始执行/check接口】")
        # 获取请求参数
        data = request.get_json()
        if not data:
            logger.error("未提供JSON数据")
            return jsonify({"error": "No JSON data provided"}), 400
        
        # 验证鉴权参数
        auth_params = {
            "Auth": data.get("Auth"),
            "Timestamp": data.get("Timestamp"),
            "User": data.get("User")
        }
        
        logger.info("【鉴权】")
        if not validate_auth_params(auth_params):
            logger.error("认证失败")
            return jsonify({"error": "Authentication failed"}), 401
        logger.info("认证成功")
        
        # 验证必要参数
        gray_domain = data.get('gray_domain')
        gray_swim_lane = data.get('gray_swim_lane')
        gray_ups = data.get('gray_ups')
        
        if not gray_domain or not gray_swim_lane or not gray_ups:
            logger.error("缺少必要参数: gray_domain, gray_swim_lane 或 gray_ups")
            return jsonify({"error": "Missing required parameters: gray_domain and gray_swim_lane and gray_ups"}), 400
        
        # 第一步：Minion连接检查
        logger.info("【第一步：Minion connect检查】")
        unreach_node_flag =check_nodegroup_connectivity()
        if unreach_node_flag==False:
            logger.warning("存在节点与salt-master连接失败")
            return jsonify({
                "data": "Minion connect failed ",
            }), 207
        logger.info("【第一步：检查目标文件是否存在】")
        logger.info("【config 文件是否存在】")
        config_file_exist_flag = config_file_exist()
        
        logger.info("【log 文件是否存在】")
        log_file_exist_flag = log_file_exist()
        
        if config_file_exist_flag == True:
            logger.warning("config文件不存在")
            return jsonify({
                "data": "config file not exist",
            }), 404
        elif log_file_exist_flag == True:
            logger.warning("log文件不存在")
            return jsonify({
                "data": "log file not exist",
            }), 404
        
        # 第二步：配置文件检查
        logger.info("【第二步：配置文件检查】")
        raw_output_config = run_salt_command_config(gray_domain, gray_swim_lane, gray_ups)
        merged_json_config = merge_json_strings_config(raw_output_config)
        config_analysis_result = analyze_salt_results_config(merged_json_config)
        logger.info("配置分析结果:\n%s", json.dumps(config_analysis_result, indent=4, ensure_ascii=False))
        
        # 第三步：错误日志检查
        logger.info("【第三步：错误日志检查】")
        raw_output_log = run_salt_command_log()
        merged_json_log = merge_json_strings_log(raw_output_log)
        log_analysis = analyze_log_data_log(merged_json_log)
        log_check_result = check_gray_route_logs_log(log_analysis)
        logger.info("日志检查结果:\n%s", json.dumps(log_check_result, indent=4, ensure_ascii=False))
        
        # 第四步：汇总结果
        logger.info("【第四步：接口输出结果】")
        
        flag = True
        if log_check_result["cluster_check_log_result"] == False:
            flag = False
        if config_analysis_result["cluster_check_config_result"] == False:
            flag = False
            
        json_result = {
            "result": flag,
            "check_config": config_analysis_result,
            "check_log": log_check_result
        }
        logger.info("最终结果:\n%s", json.dumps(json_result, indent=4, ensure_ascii=False))
        logger.info("【检查完成！】")
        
        # 返回最终结果
        return jsonify({
            "data": json_result,
        }), 200
        
    except Exception as e:
        # 记录错误日志
        error_msg = "执行检查时出错: {}\n{}".format(str(e), traceback.format_exc())
        logger.error(error_msg)
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc().split('\n')
        }), 500
        
@app.route('/delete', methods=['POST'])
def execute_delete():
    try:
        logger.info("【开始执行/delete接口】")
        # 获取请求参数
        data = request.get_json()
        if not data:
            logger.error("未提供JSON数据")
            return jsonify({"error": "No JSON data provided"}), 400
        
        # 验证鉴权参数
        auth_params = {
            "Auth": data.get("Auth"),
            "Timestamp": data.get("Timestamp"),
            "User": data.get("User")
        }
        
        logger.info("【鉴权】")
        if not validate_auth_params(auth_params):
            logger.error("认证失败")
            return jsonify({"error": "Authentication failed"}), 401
        logger.info("认证成功")
        
        # 验证必要参数
        gray_domain = data.get('gray_domain')  
        if not gray_domain:
            logger.error("缺少必要参数: gray_domain")
            return jsonify({"error": "Missing required parameters: gray_domain"}), 400
        
        # 第一步：Minion连接检查
        logger.info("【第一步：Minion connect检查】")
        unreach_node_flag=check_nodegroup_connectivity()
        if unreach_node_flag==False:
            logger.warning("存在节点与salt-master连接失败")
            return jsonify({
                "data": "Minion connect failed ",
            }), 207
            
        logger.info("【第一步：检查目标文件是否存在】")
        logger.info("【config 文件是否存在】")
        config_file_exist_flag = config_file_exist()
        
        if config_file_exist_flag == True:
            logger.warning("config文件不存在")
            return jsonify({
                "data": "config file not exist",
            }), 404

        # 第二步：配置文件检查
        logger.info("【第二步：是否删除检查】")
        raw_output_config = run_delete_salt(gray_domain)
        merged_json_config = merge_delete_json(raw_output_config)
        delete_analysis_result = analyze_delete_results(merged_json_config)
        logger.info("删除分析结果:\n%s", json.dumps(delete_analysis_result, indent=4, ensure_ascii=False))
        
        # 第四步：汇总结果
        logger.info("【第四步：接口输出结果】")
        
        flag = True
        if delete_analysis_result["cluster_check_config_result"] == False:
            flag = False
            
        json_result = {
            "cluster_check_result": flag,
            "check_config": delete_analysis_result,
        }
        logger.info("最终结果:\n%s", json.dumps(json_result, indent=4, ensure_ascii=False))
        logger.info("【“删除配置”检查完成！】")
        
        # 返回最终结果
        return jsonify({
            "data": json_result,
        }), 200
        
    except Exception as e:
        # 记录错误日志
        error_msg = "执行删除检查时出错: {}\n{}".format(str(e), traceback.format_exc())
        logger.error(error_msg)
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc().split('\n')
        }), 500

if __name__ == '__main__':
    # 配置Flask应用的日志
    flask_log_handler = RotatingFileHandler(
        'flask.log', maxBytes=10*1024*1024, backupCount=3, encoding='utf-8'
    )
    flask_log_handler.setLevel(logging.INFO)
    flask_log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    flask_log_handler.setFormatter(flask_log_formatter)
    
    # 移除默认的Flask日志处理器，添加我们自定义的
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    app.logger.addHandler(flask_log_handler)
    app.logger.setLevel(logging.INFO)
    
    logger.info("Flask应用启动")
    app.run(host='127.0.0.1', port=10025, debug=False)