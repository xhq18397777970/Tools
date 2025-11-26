# -*- coding: utf-8 -*-
import json
import re
import subprocess
#!/usr/bin/env python3
import salt.client

global flag
# ==================== 第一部分：【Minion connection检查】 ====================
def check_nodegroup_connectivity(nodegroup_name="gray_list"):
    """
    检查指定 nodegroup 的 Minion 连接状态，并返回连接失败的 Minion 列表
    :param nodegroup_name: 要检查的 nodegroup 名称（默认 'gray_list'）
    :return: list[str] 连接失败的 Minion ID 列表（全部正常则返回 []）
    """
    local = salt.client.LocalClient()
    unreachable_minions = []

    try:
        # 执行 test.ping 测试
        result = local.cmd(
            tgt=nodegroup_name,
            fun='test.ping',
            tgt_type='nodegroup',
            timeout=5  # 超时时间（秒）
        )

        # 收集连接失败的 Minion
        for minion_id, status in result.items():
            if status is not True:  # 包括 False、None 或其他非 True 值
                unreachable_minions.append(minion_id)

        # 打印结果（可选，根据需求保留或移除）
        print("\n==== Nodegroup [{}] 连接状态检查:\n".format(nodegroup_name))
        print("=" * 50)
        for minion_id, status in result.items():
            if status is True:
                print("[✓] {}: 连接正常".format(minion_id))
            else:
                print("[✗] {}: 连接失败或未响应".format(minion_id))

        if unreachable_minions:
            print("\n警告: 以下 Minion 未响应:")
            for minion in unreachable_minions:
                print("  - {}".format(minion))
        else:
            print("\n==== 所有 Minion 连接正常！\n")

    except Exception as e:
        print("检查失败: {}".format(str(e)))
        # 发生异常时返回 None 或根据需求调整（这里返回空列表保持一致性）
        return []

    return unreachable_minions
# ==================== 第二部分：【检查文件是否存在】 ====================
#检查是否目标文件（/export/servers/jfe/conf/localconfs/all_gray_ups.json）是否存在
def config_file_exist():

    try:
        cmd = [
            "sudo", "salt", "-N", "gray_list", "file.file_exists", "/export/servers/jfe/conf/localconfs/all_gray_ups.json","--out=json"
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        
        matching_lines = []
        found = False
        lines = stdout.split('\n')
    
        for line in lines:
            if re.search(r'False', line, re.IGNORECASE):  # 不区分大小写匹配
                matching_lines.append(line.strip())
                found = True
        if found is True:
            print("NO! config file not exist\n",matching_lines)
        else:
            print("OK, All nodes exist config file\n")
        return found
    
    except Exception as e:
        return "Error: {0}".format(str(e))

def log_file_exist():

    try:
        cmd = [
            "sudo", "salt", "-N", "gray_list", "file.file_exists", "/export/servers/jfe/logs/error.log","--out=json"
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        
        matching_lines = []
        found = False
        lines = stdout.split('\n')
    
        for line in lines:
            if re.search(r'False', line, re.IGNORECASE):  # 不区分大小写匹配
                matching_lines.append(line.strip())
                found = True
        if found is True:
            print("NO! log file not exist\n",matching_lines)
        else:
            print("OK, All nodes exist log file\n")
        return found
    
    except Exception as e:
        return "Error: {0}".format(str(e))
# ==================== 1.1：Salt命令  ====================
def run_salt_command_config(gray_domain, gray_swim_lane,gray_ups):
    """
    执行 Salt 命令并返回原始字符串输出（用于配置检查）
    
    参数:
        gray_domain (str):域名，跟工单中域名一致  如  "color.7fresh.com"   
        gray_swim_lane (str): 泳道code，跟工单中泳道Code一致 如  "GRAY_RETAIL_MAIN"
        gray_ups (str): 灰度集群，跟工单中灰度集群一致    如 "gray_retail_main" 
    
    返回:
        str: Salt 命令的原始输出（stdout + stderr）
    """
    try:
        cmd = [
            "sudo", "salt", "-N", "gray_list", "state.apply", "check_resolv_template",
            "pillar={\"gray_domain\": \"%s\", \"gray_swim_lane\": \"%s\",\"gray_ups\": \"%s\"}" % (gray_domain, gray_swim_lane,gray_ups),
            "--out=json"
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        
        return stdout + stderr  # 返回原始字符串（可能包含 JSON 或错误信息）
    
    except Exception as e:
        return "Error: {0}".format(str(e))
# ==================== 1.2：Salt输出转为JSON （过滤"ERROR"）  ====================
def merge_json_strings_config(input_str):
    lines = input_str.split('\n')
    # 过滤掉包含"ERROR"的行（不区分大小写）
    filtered_lines = [line for line in lines if 'ERROR' not in line]
    # 重新组合成字符串
    temp_line='\n'.join(filtered_lines)

    fixed_str = temp_line.replace("}\n{", "},\n{")
    fixed_str = "[" + fixed_str.replace("\n", "") + "]"  # 变成 JSON 数组
    
    try:
        json_array = json.loads(fixed_str)
        merged_data = {}
        for item in json_array:
            merged_data.update(item)
        return merged_data
    except ValueError as e:
        print("Error parsing fixed JSON string: {}".format(e))
        return {}
# ==================== 1.3：整合每个灰度节点结果 （过滤失败的，并保存错误配置信息）  ====================
def analyze_salt_results_config(salt_results):
    global flag 
    analysis_result = {
        "cluster_check_config_result": True,
        "failed_nodes": [],
        "error_log": []
    }
    
    for node, states in salt_results.items():
        state_name, state_result = next(iter(states.items()))
        
        if not state_result.get("result", True):
            analysis_result["failed_nodes"].append(node)
            analysis_result["cluster_check_config_result"] = False
            
            analysis_result["error_log"].append({
                "node": node,
                "node_result": False,
                "config": state_result.get("comment", "No error details available")
            })
    if analysis_result["cluster_check_config_result"] is not True:
        flag=False
    else:
        flag=True

    return analysis_result  # 直接返回字典，而不是 JSON 字符串


# ==================== 第三部分：【日志检查】 ====================
# ==================== 2.1：Salt命令  ====================
def run_salt_command_log():
    try:
        cmd = [
            "sudo", "salt", "-N", "gray_list", "state.apply", "check_log",
            "--out=json"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        
        return stdout + stderr  # 返回原始字符串（可能包含 JSON 或错误信息）
    
    except Exception as e:
        return "Error: {0}".format(str(e))
# ==================== 2.2：Salt输出转为JSON （过滤"ERROR"）  ====================
def merge_json_strings_log(input_str):
    lines = input_str.split('\n')
    # 过滤掉包含"ERROR"的行（不区分大小写）
    filtered_lines = [line for line in lines if 'ERROR' not in line.upper()]
    # 重新组合成字符串
    temp_line = '\n'.join(filtered_lines)
    
    # 处理可能的JSON片段拼接
    fixed_str = temp_line.replace("}\n{", "},\n{")
    if not fixed_str.startswith('['):
        fixed_str = "[" + fixed_str
    if not fixed_str.endswith(']'):
        fixed_str = fixed_str + "]"
    
    try:
        json_array = json.loads(fixed_str)
        merged_data = {}
        for item in json_array:
            merged_data.update(item)
        return merged_data
    except ValueError as e:
        print("Error parsing fixed JSON string: {}".format(e))
        return {}
# ==================== 1.3：合并日志  ====================
def analyze_log_data_log(data_dict):
    result = {
        "log_content": []
    }
    
    for node, node_data in data_dict.items():
        for cmd_id, cmd_data in node_data.items():
            stdout = cmd_data['changes'].get('stdout', '')
            if stdout:  # 只添加有实际日志输出的节点
                result["log_content"].append({node: stdout})
    
    return json.dumps(result, indent=4, ensure_ascii=False)

# ==================== 2.4：整合灰度节点 日志信息  ====================
def check_gray_route_logs_log(log_analysis_json):
    global flag 
    try:
        log_data = json.loads(log_analysis_json)
    except ValueError as e:
        return {
            "error": "Invalid JSON input",
            "details": str(e)
        }
    
    result = {
        "cluster_check_log_result": True,
        "failed_nodes": [],
        "error_log": []
    }
    for node_entry in log_data.get("log_content", []):
        node_name, node_content = next(iter(node_entry.items()))
        lines = node_content.split('\n')
        failed_lines = []
        
        for line in lines:
            if "all_gray_route.lua" in line:
                failed_lines.append(line.strip())
        
        if failed_lines:
            result["cluster_check_log_result"] = False
            result["failed_nodes"].append(node_name)
            result["error_log"].append({
                "node": node_name,
                "node_result": False,
                "error_log": "\n".join(failed_lines)
            })
    if result["cluster_check_log_result"] is not True:
        flag=False
    else:
        flag=True
    return result  # 直接返回字典，而不是 JSON 字符串

# ==================== 第四步：汇总结果，返回json  ====================
# def final_check():
#     global flag 
#      # 配置、日志 检查结果（boolean）
  
#     json_result = {
#         "cluster_check_result": flag,
#         "check_config":config_analysis_result,
#         "check_log":log_check_result
#     }
#     return json_result

# ==================== 主程序 ====================
if __name__ == "__main__":
    print("【第一步：Minion connect检查】")
    check_nodegroup_connectivity()
    
    # 传递参数
    gray_domain = "color.7fresh.com"
    gray_swim_lane = "GRAY_RETAIL_MAIN"
    gray_ups="gray_retail_main"
    
    print("【第一步：检查目标文件是否存在】")
    print("【config 文件是否存在】")
    config_file_exist()
    
    print("【log 文件是否存在】")
    log_file_exist()
    
    print("【第二步：配置文件检查】")
    raw_output_config = run_salt_command_config(gray_domain, gray_swim_lane,gray_ups)
    merged_json_config = merge_json_strings_config(raw_output_config)
    config_analysis_result = analyze_salt_results_config(merged_json_config)  # 保存结果
    print(json.dumps(config_analysis_result, indent=4, ensure_ascii=False))
    
    # 执行日志检查部分
    print("\n【第三步：错误日志检查】")
    raw_output_log = run_salt_command_log()
    merged_json_log = merge_json_strings_log(raw_output_log)
    log_analysis = analyze_log_data_log(merged_json_log)
    log_check_result = check_gray_route_logs_log(log_analysis)  # 保存结果
    print(json.dumps(log_check_result, indent=4, ensure_ascii=False))
    
    #接口输出json
    print("\n【第四步：接口输出结果】")
    
    # print(json.dumps(final_check(),indent=4,ensure_ascii=False))
    
