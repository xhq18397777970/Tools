import ipaddress
import json
import os
from typing import List, Union, Tuple
# ==============================================================================
# 第一部分功能模块：从原始数据提取IP并合并到JSON
# ==============================================================================
 
def extract_ip_parents(json_data):
    """从单个JSON数据项中提取符合条件的IP网段。"""
    ip_segments = []
    
    if not ('data' in json_data and 'list' in json_data['data']):
        return ip_segments
    
    for item in json_data['data']['list']:
        try:
            if item.get('logic_idc_first_level') is not True:
                continue
            if item.get('ip_type') != '私网地址':
                continue
            if item.get('is_core') is not True:
                continue
            if item.get('use_type_strval') == "互联地址":
                continue
            
            business_list = item.get('business', [])
            if not any(bus.get('business_name') in ['商城', '大数据','数科消金','数字科技','企业信息化','物流','健康','安联保险','信息安全','客服','人工智能'] for bus in business_list):
                continue
            
            ip_segment = item.get('ip_segment_all')
            if ip_segment and isinstance(ip_segment, str):
                ip_segments.append(ip_segment.strip())
                
        except (AttributeError, KeyError, TypeError):
            continue
    
    return ip_segments
 
def parse_network(network_str: str) -> Union[ipaddress.IPv4Network, Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]]:
    """解析网络字符串，支持CIDR和IP范围格式。"""
    network_str = network_str.strip()
    try:
        if '/' in network_str:
            return ipaddress.IPv4Network(network_str, strict=False)
    except ValueError:
        pass
    
    if '-' in network_str:
        start_str, end_str = network_str.split('-', 1)
        try:
            start_ip = ipaddress.IPv4Address(start_str.strip())
            end_ip = ipaddress.IPv4Address(end_str.strip())
            if start_ip <= end_ip:
                return (start_ip, end_ip)
        except ValueError:
            pass
    
    try:
        ip = ipaddress.IPv4Address(network_str)
        return ipaddress.IPv4Network(f"{ip}/32", strict=False)
    except ValueError:
        pass
    
    raise ValueError(f"无法解析的网络格式: {network_str}")
 
def network_to_range(network: Union[ipaddress.IPv4Network, Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]]) -> Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]:
    """将网络对象转换为IP范围元组"""
    if isinstance(network, ipaddress.IPv4Network):
        return (network.network_address, network.broadcast_address) 
    else:
        return network
 
def merge_ipv4_networks(networks: List[str]) -> List[str]:
    """合并IPv4网段列表。"""
    # （此函数在你的逻辑中被注释掉了，但保留以供将来使用）
    if not networks: return []
    ranges = []
    for network_str in networks:
        network = parse_network(network_str)
        start, end = network_to_range(network)
        ranges.append((start, end))
    
    ranges.sort(key=lambda x: x[0])
    
    merged_ranges = []
    if not ranges: return []
    current_start, current_end = ranges[0]
    
    for i in range(1, len(ranges)):
        next_start, next_end = ranges[i]
        if current_end + 1 >= next_start:
            if next_end > current_end: current_end = next_end
        else:
            merged_ranges.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    merged_ranges.append((current_start, current_end))
    
    result = []
    for start, end in merged_ranges:
        cidr_list = list(ipaddress.summarize_address_range(start, end))
        result.extend([str(cidr) for cidr in cidr_list])
    
    return result
 
def process_json_files_in_folder(folder_path, output_file):
    """处理单个文件夹中的所有JSON文件，提取IP网段并保存结果。"""
    all_ip_parents = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    ip_parents = extract_ip_parents(json_data)
                    all_ip_parents.extend(ip_parents)
                    print(f"    - 已处理文件: {filename}, 提取到 {len(ip_parents)} 个IP网段")
            except json.JSONDecodeError:
                print(f"    - 错误: 文件 {filename} 不是有效的JSON格式，已跳过")
            except Exception as e:
                print(f"    - 错误: 处理文件 {filename} 时发生异常 - {e}")
    
    # =================================================================
    # 【修改部分】在写入文件前，过滤掉以 '100.' 开头的IP网段
    # =================================================================
    # 使用列表推导式创建一个新列表，只包含不以 '100.' 开头的网段
    filtered_networks = [net for net in all_ip_parents if not net.startswith('100.')]
    
    # 更新日志输出，显示过滤前后的数量，方便你验证
    print(f"    -> 过滤前网段总数: {len(all_ip_parents)}")
    print(f"    -> 已剔除 '100.*' 网段，过滤后网段总数: {len(filtered_networks)}")
    
    # 将过滤后的列表赋值给最终的变量，保持原代码结构清晰
    merged_networks = filtered_networks
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"merged_networks": merged_networks}, f, indent=2, ensure_ascii=False)
        print(f"  -> 处理完成，结果已保存到 {output_file} (共 {len(merged_networks)} 个网段)")
    except Exception as e:
        print(f"  -> 错误: 保存结果到 {output_file} 时失败 - {e}")
 
def process_all_folders(input_root_folder, output_root_folder):
    """批量处理输入根文件夹中的所有子文件夹。"""
    print(f"第一步：开始处理文件夹 '{input_root_folder}'...")
    os.makedirs(output_root_folder, exist_ok=True)
    
    for folder_name in os.listdir(input_root_folder):
        input_folder_path = os.path.join(input_root_folder, folder_name)
        if os.path.isdir(input_folder_path):
            output_file_path = os.path.join(output_root_folder, f"{folder_name}.json")
            print(f"\n  正在处理子文件夹: {folder_name}")
            process_json_files_in_folder(input_folder_path, output_file_path)
    print("\n第一步处理完成。")
 
# ==============================================================================
# 第二部分功能模块：将JSON转换为ACL格式
# ==============================================================================
 
def convert_json_to_acl(json_file_path: str, acl_file_path: str):
    """将包含网络列表的 JSON 文件转换为指定的 ACL 格式。"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"    - 警告: 无法读取或解析文件 '{os.path.basename(json_file_path)}', 原因: {e} (跳过)")
        return
 
    networks = data.get('merged_networks', [])
    network_lines = "\n".join([f"  {net};" for net in networks])
    acl_content = f"""acl "acl-" {{{network_lines}}};"""
 
    try:
        with open(acl_file_path, 'w', encoding='utf-8') as f:
            f.write(acl_content)
        print(f"    - 转换成功: '{os.path.basename(json_file_path)}' -> '{os.path.basename(acl_file_path)}'")
    except IOError as e:
        print(f"    - 错误: 无法写入文件 '{os.path.basename(acl_file_path)}'。原因: {e}")
 
def convert_all_jsons_in_folder(input_folder: str, output_folder: str):
    """批量转换一个文件夹内的所有 JSON 文件为 ACL 文件。"""
    print(f"\n第二步：开始将 '{input_folder}' 中的JSON转换为ACL...")
    os.makedirs(output_folder, exist_ok=True)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.json'):
            input_file_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + '.acl'
            output_file_path = os.path.join(output_folder, output_filename)
            convert_json_to_acl(input_file_path, output_file_path)
    print("\n第二步处理完成。")
 
# ==============================================================================
# 第三部分功能模块：检查ACL文件之间的IP重叠
# ==============================================================================
 
def load_ip_networks(filename):
    """从ACL文件中加载所有IP网络对象。"""
    ip_networks = []
    with open(filename, 'r') as file:
        in_acl_block = False
        for line in file:
            line = line.strip()
            if line.startswith('acl'):
                in_acl_block = True
                continue
            if line.endswith('};'):
                in_acl_block = False
                continue
            if in_acl_block and ';' in line:
                network_str = line.split(';')[0].strip()
                try:
                    ip_networks.append(ipaddress.ip_network(network_str, strict=False))
                except ValueError:
                    # 忽略无法解析的行
                    pass
    return ip_networks
 
def check_for_overlaps(acl1_filename, acl2_filename):
    """检查两个ACL文件之间的IP重叠。"""
    acl1_networks = load_ip_networks(acl1_filename)
    acl2_networks = load_ip_networks(acl2_filename)
    overlaps = []
    for network1 in acl1_networks:
        for network2 in acl2_networks:
            if network1.overlaps(network2):
                overlaps.append((network1, network2))
    return overlaps
 
def run_overlap_check(acl_dir):
    """运行所有ACL文件的重叠检查。"""
    print(f"\n第三步：开始检查 '{acl_dir}' 目录下的ACL文件重叠...")
    files = [os.path.join(acl_dir, f) for f in os.listdir(acl_dir)
            if os.path.isfile(os.path.join(acl_dir, f)) and f.endswith('.acl')]
    
    if not files:
        print(f"在目录 {acl_dir} 中没有找到任何.acl文件，检查结束。")
        return
 
    found_any_overlap = False
    for i in range(len(files)):
        for j in range(i+1, len(files)):
            overlaps = check_for_overlaps(files[i], files[j])
            if overlaps:
                found_any_overlap = True
                file1_name = os.path.basename(files[i])
                file2_name = os.path.basename(files[j])
                print(f"\n  [发现重叠] [{file1_name}] 和 [{file2_name}] 的交集IP范围如下：")
                for net1, net2 in overlaps:
                    print(f"    - {net1} 与 {net2} 有交集")
    
    if not found_any_overlap:
        print("\n  [恭喜] 未发现任何ACL文件之间存在IP重叠。")
    print("\n第三步检查完成。")
 
# ==============================================================================
# 主执行流程
# ==============================================================================
 
if __name__ == "__main__":
    # --- 配置路径 ---
    BASE_DIR = "/Users/xiehanqi.jackson/Documents/CODE"
    original_data_dir = os.path.join(BASE_DIR, 'original_data')
    json_results_dir = os.path.join(BASE_DIR, 'json_results')
    output_acl_folder = os.path.join(BASE_DIR, 'acl')
 
    # --- 检查起始输入是否存在 ---
    if not os.path.isdir(original_data_dir):
        print(f"错误：唯一的输入文件夹 '{original_data_dir}' 不存在或不是一个有效的目录！")
        print("请确保该文件夹存在且包含你的原始数据文件。")
    else:
        # --- 按顺序执行所有步骤 ---
        process_all_folders(original_data_dir, json_results_dir)
        convert_all_jsons_in_folder(json_results_dir, output_acl_folder)
        run_overlap_check(output_acl_folder)
 
        print("\n" + "="*50)
        print("所有流程执行完成！")
        print("="*50)