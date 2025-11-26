import ipaddress
import json
import os
import ipaddress
from typing import List, Union, Tuple

def extract_ip_parents(json_data):
    ip_segments = []
    
    # 检查数据是否包含'data'和'list'字段
    if not ('data' in json_data and 'list' in json_data['data']):
        return ip_segments  # 如果数据格式不符，直接返回空列表
    
    for item in json_data['data']['list']:
        try:
            # 1. 检查 logic_idc_first_level 是否为 True
            if item.get('logic_idc_first_level') is not True:
                continue
            
            # 2. 检查 ip_type 是否为 "私网地址"
            if item.get('ip_type') != '私网地址':
                continue
            
            # 1. 检查 is_core (是否参与统计) 是否为 True
            if item.get('is_core') is not True:
                continue
            
            # 3. 检查 use_type_strval 是否不等于 "互联地址"
            if item.get('use_type_strval') == "互联地址":
                continue
            
            # 4. 检查 business 列表中是否有 business_name 为 "商城" 或 "大数据"
            business_list = item.get('business', [])
            if not any(bus.get('business_name') in ['商城', '大数据','数科消金','数字科技','企业信息化','物流','健康','安联保险','信息安全','客服','人工智能'] for bus in business_list):
                continue
            
            # 6. 检查 ip_segment_all 是否存在且非空
            ip_segment = item.get('ip_segment_all')
            if ip_segment and isinstance(ip_segment, str):
                ip_segments.append(ip_segment.strip())  # 去除前后空格
                
        except (AttributeError, KeyError, TypeError):
            # 如果 business 不是列表、缺少字段或 cn_name 不是字符串，跳过
            continue
    
    return ip_segments

#网段合并
def parse_network(network_str: str) -> Union[ipaddress.IPv4Network, Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]]:
    """
    解析网络字符串，支持CIDR和IP范围格式
    返回IPv4Network对象或(start_ip, end_ip)元组
    """
    network_str = network_str.strip()
    
    # 尝试解析为CIDR
    try:
        if '/' in network_str:
            return ipaddress.IPv4Network(network_str, strict=False)
    except ValueError:
        pass
    
    # 尝试解析为IP范围 (start-end)
    if '-' in network_str:
        start_str, end_str = network_str.split('-', 1)
        try:
            start_ip = ipaddress.IPv4Address(start_str.strip())
            end_ip = ipaddress.IPv4Address(end_str.strip())
            if start_ip <= end_ip:
                return (start_ip, end_ip)
        except ValueError:
            pass
    
    # 尝试解析为单个IP
    try:
        ip = ipaddress.IPv4Address(network_str)
        return ipaddress.IPv4Network(f"{ip}/32", strict=False)
    except ValueError:
        pass
    
    raise ValueError(f"无法解析的网络格式: {network_str}")

def network_to_range(network: Union[ipaddress.IPv4Network, Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]]) -> Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]:
    """
    将网络对象转换为IP范围元组 (start, end)
    """
    if isinstance(network, ipaddress.IPv4Network):
        return (network.network_address, network.broadcast_address) 
    else:
        return network

def merge_ipv4_networks(networks: List[str]) -> List[str]:
    """
    合并IPv4网段列表
    """
    if not networks:
        return []
    
    if len(networks) == 1:
        network = parse_network(networks[0])
        if isinstance(network, tuple):
            start, end = network
            return [str(ip) for ip in ipaddress.summarize_address_range(start, end)]
        else:
            return [str(network)]
    
    # 1. 解析所有网络为范围
    ranges = []
    for network_str in networks:
        network = parse_network(network_str)
        start, end = network_to_range(network)
        ranges.append((start, end))
    
    # 2. 按起始IP排序
    ranges.sort(key=lambda x: x[0])
    
    # 3. 合并重叠或相邻的范围
    merged_ranges = []
    current_start, current_end = ranges[0]
    
    for i in range(1, len(ranges)):
        next_start, next_end = ranges[i]
        
        # 检查是否可以合并（重叠或相邻）
        current_end_plus_1 = current_end + 1
        if current_end_plus_1 >= next_start:
            if next_end > current_end:
                current_end = next_end
        else:
            merged_ranges.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    # 添加最后一个范围
    merged_ranges.append((current_start, current_end))
    
    # 4. 将合并后的范围转换回CIDR格式
    result = []
    for start, end in merged_ranges:
        cidr_list = list(ipaddress.summarize_address_range(start, end))
        result.extend([str(cidr) for cidr in cidr_list])
    
    return result

def process_json_files_in_folder(folder_path, output_file):
    """
    处理单个文件夹中的所有JSON文件，提取IP网段并保存结果
    """
    all_ip_parents = []
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    ip_parents = extract_ip_parents(json_data)
                    all_ip_parents.extend(ip_parents)
                    print(f"已处理文件: {filename}, 提取到 {len(ip_parents)} 个IP网段")
            except json.JSONDecodeError:
                print(f"错误: 文件 {filename} 不是有效的JSON格式，已跳过")
            except Exception as e:
                print(f"错误: 处理文件 {filename} 时发生异常 - {e}")
    
    
    # # 合并所有IP网段
    # merged_networks = merge_ipv4_networks(all_ip_parents)
    
    # 不合并网段，直接使用原始数据
    merged_networks = all_ip_parents
    
    # 将结果保存到输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"merged_networks": merged_networks}, f, indent=2, ensure_ascii=False)
        print(f"处理完成，结果已保存到 {output_file}")
        print(f"共提取到 {len(merged_networks)} 个IP网段")
    except Exception as e:
        print(f"错误: 保存结果到 {output_file} 时失败 - {e}")

def process_all_folders(input_root_folder, output_root_folder):
    """
    批量处理输入根文件夹中的所有子文件夹
    
    参数:
        input_root_folder (str): 输入根文件夹路径
        output_root_folder (str): 输出根文件夹路径
    """
    # 确保输出根文件夹存在
    if not os.path.exists(output_root_folder):
        os.makedirs(output_root_folder)
        print(f"创建输出目录: {output_root_folder}")
    
    # 遍历输入根文件夹中的所有子文件夹
    for folder_name in os.listdir(input_root_folder):
        input_folder_path = os.path.join(input_root_folder, folder_name)
        
        # 只处理文件夹，忽略文件
        if os.path.isdir(input_folder_path):
            # 构建对应的输出文件路径
            output_file_name = f"{folder_name}.json"
            output_file_path = os.path.join(output_root_folder, output_file_name)
            
            print(f"\n开始处理文件夹: {folder_name}")
            print(f"输入路径: {input_folder_path}")
            print(f"输出路径: {output_file_path}")
            
            # 处理该文件夹中的所有JSON文件
            process_json_files_in_folder(input_folder_path, output_file_path)
        else:
            print(f"跳过非文件夹: {folder_name}")

if __name__ == "__main__":
    # 配置输入和输出根文件夹路径
    input_root_folder = "/Users/xiehanqi.jackson/Documents/CODE/11-26/original_data"
    output_root_folder = "/Users/xiehanqi.jackson/Documents/CODE/11-26/json_results"
    
    if os.path.isdir(input_root_folder):
        process_all_folders(input_root_folder, output_root_folder)
        print(f"\n所有文件夹处理完成！结果保存在: {output_root_folder}")
    else:
        print("错误: 指定的输入根文件夹路径不存在！")