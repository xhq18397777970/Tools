# -*- coding: utf-8 -*-
import json
import re
import subprocess
#!/usr/bin/env python3
import salt.client


# ==================== 第一部分：【Minion connection检查】 ====================
def check_nodegroup_connectivity(nodegroup_name="gray_list"):
    """
    检查指定 nodegroup 的 Minion 连接状态
    :param nodegroup_name: 要检查的 nodegroup 名称（默认 'gray_list')
    """
    # 创建 Salt LocalClient 实例
    local = salt.client.LocalClient()

    try:
        # 使用 nodegroup 目标执行 test.ping
        result = local.cmd(
            tgt=nodegroup_name,
            fun='test.ping',
            tgt_type='nodegroup',
            timeout=5  # 超时时间（秒）
        )
        print("\n==== Nodegroup [{}] 连接状态检查:\n".format(nodegroup_name))
        print("=" * 50)
        for minion_id, status in result.items():
            if status is True:
                print("[✓] {}: 连接正常".format(minion_id))
            else:
                print("[✗] {}: 连接失败或未响应".format(minion_id))
        # 检查是否有未响应的 Minion
        unreachable = [minion for minion, status in result.items() if status is not True]
        if unreachable:
            print("\n警告: 以下 Minion 未响应:")
            for minion in unreachable:
                print("  - {minion}".format(minion_id))
        else:
            print("\n==== 所有 Minion 连接正常！\n")

    except Exception as e:
        print("检查失败: {}".format(str(e)))
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

# ==================== 第二部分：【配置检查】 ====================
# ==================== 1.1：Salt命令  ====================
def run_delete_salt(gray_domain):

    try:
        cmd = [
            "sudo", "salt", "sq-pub-jfe1-01.sq.jd.local", "state.apply", "check_delete",
            "pillar={\"gray_domain\": \"%s\"}" % (gray_domain),
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
def merge_delete_json(input_str):
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
def analyze_delete_results(salt_results):

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
    return analysis_result  # 直接返回字典，而不是 JSON 字符串


# ==================== 主程序 ====================
if __name__ == "__main__":
    print("【第一步：Minion connect检查】")
    check_nodegroup_connectivity()
    
    # 传递参数
    gray_domain = "113"

    print("【第一步：检查目标文件是否存在】")
    print("【config 文件是否存在】")
    config_file_exist()


    print("【第二步：配置文件检查】")
    raw_output_config = run_delete_salt(gray_domain)
    merged_json_config = merge_delete_json_strings_config(raw_output_config)
    config_analysis_result = analyze_delete_results(merged_json_config)  # 保存结果
    print(json.dumps(config_analysis_result, indent=4, ensure_ascii=False))

    #接口输出json
    print("\n【第四步：接口输出结果】")
    