# -*- coding: utf-8 -*-
import json
import re
import subprocess
#!/usr/bin/env python3
import salt.client

global flag
# ==================== 第一部分：【Minion connection检查】 ====================
def check_nodegroup_connectivity(minion_id='sq-pub-jfe1-01.sq.jd.local'):
    """
    检查指定 Minion 的连接状态，失败时返回 False，成功返回 True
    :param minion_id: 要检查的 Minion ID（如 'gray-minion-01'）
    :return: bool 连接状态（True=正常，False=失败）
    """
    local = salt.client.LocalClient()
 
    try:
        # 对单个 Minion 执行 test.ping
        result = local.cmd(
            tgt=minion_id,
            fun='test.ping',
            tgt_type='glob',  # 使用 glob 匹配单个 Minion
            timeout=5        # 超时时间（秒）
        )
 
        # 检查返回结果
        if minion_id in result:
            status = result[minion_id]
            if status is True:
                print("[✓] {}: 连接正常".format(minion_id))
                return True
            else:
                print("[✗] {}: 连接失败（返回非 True 状态）".format(minion_id))
                return False
        else:
            print("[✗] {}: 无响应（可能 Minion 不存在或未运行）".format(minion_id))
            return False
 
    except Exception as e:
        print("检查失败: {}".format(str(e)))
        return False
# ==================== 第二部分：【检查文件是否存在】 ====================
#检查是否目标文件（/export/servers/jfe/conf/localconfs/all_gray_ups.json）是否存在
def config_file_exist():

    try:
        cmd = [
            "sudo", "salt", "sq-pub-jfe1-01.sq.jd.local", "file.file_exists", "/export/servers/jfe/conf/localconfs/all_gray_ups.json","--out=json"
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
            "sudo", "salt", "sq-pub-jfe1-01.sq.jd.local", "file.file_exists", "/export/servers/jfe/logs/error.log","--out=json"
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
            "sudo", "salt", "sq-pub-jfe1-01.sq.jd.local", "state.apply", "check_resolv_template",
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
            "sudo", "salt", "sq-pub-jfe1-01.sq.jd.local", "state.apply", "check_log",
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
    
