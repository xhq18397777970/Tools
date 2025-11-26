import json
import ipaddress
import json
import os
#公有云
# def extract_ip_parents(json_data):
#     ip_segments = []
    
#     # 检查数据是否包含'data'和'list'字段
#     if 'data' in json_data and 'list' in json_data['data']:
#         for item in json_data['data']['list']:
#             try:
#                 # 1. 检查 logic_idc_first_level 是否为 True
#                 if not item.get('logic_idc_first_level', False):
#                     continue
                
#                 # 2. 检查 ip_type 是否为 "私网地址"
#                 if item.get('ip_type') != '私网地址':
#                     continue
                
#                 # 3. 检查 use_type_strval 是否不是 "互联地址"
#                 if item.get('use_type_strval') == '互联地址':
#                     continue
                
#                 # 4. 检查 business 列表中是否有 business_name 为 "公有云"
#                 business_list = item.get('business', [])
#                 if not any(bus.get('business_name') == '公有云' for bus in business_list):
#                     continue
                
#                 # 5. 检查 ip_segment_all 是否存在且非空
#                 if 'ip_segment_all' in item and item['ip_segment_all']:
#                     ip_segments.append(item['ip_segment_all'].strip())  # 去除前后空格
                    
#             except (AttributeError, KeyError, TypeError):
#                 # 如果 business 不是列表、缺少字段或 cn_name 不是字符串，跳过
#                 continue
    
#     return ip_segments
# 非公有云
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
            
            # 3. 检查 use_type_strval 是否不等于 "互联地址"
            if item.get('use_type_strval') == "互联地址":
                continue
            
            # 4. 检查 business 列表中是否有 business_name 为 "商城" 或 "大数据"
            business_list = item.get('business', [])
            if not any(bus.get('business_name') in ['商城', '大数据','数科消金','云物理机','数字科技'] for bus in business_list):
                continue
            
            # 5. 检查 cn_name 是否 **既不包含 "1" 也不包含 "1"**
            # cn_name = item.get('logic_name')
            # if not isinstance(cn_name, str) or ("1" in cn_name or "润惠" in cn_name):
            #     continue
            
            # 5. 检查 logic_name 是否包含 "1"
            cn_name = item.get('logic_name')
            if not isinstance(cn_name, str) or "黄村" not in cn_name:
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
def merge_ipv4_networks(networks):
    """
    合并相邻或重叠的IPv4网段（迭代版，避免递归深度问题）
    """
    if not networks: 
        return []
    
    # 过滤无效网段并转换为 IPv4Network 对象
    network_objects = []
    for network in networks:
        if not network.strip():
            continue
        try:
            net = ipaddress.IPv4Network(network, strict=False)
            network_objects.append(net)
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            print(f"Warning: 跳过无效的IP网段 '{network}'")
            continue
    
    if not network_objects:
        return []
    
    # 初始排序
    sorted_networks = sorted(network_objects, key=lambda x: x.network_address)
    
    # 迭代合并，直到无法进一步合并
    changed = True
    while changed:
        changed = False
        merged_networks = []
        current_network = sorted_networks[0]
        
        for network in sorted_networks[1:]:
            # 检查是否可以合并（重叠、相邻或包含）
            if (current_network.supernet_of(network) or 
                current_network.overlaps(network) or
                current_network.broadcast_address + 1 == network.network_address):
                # 合并网段
                min_addr = min(current_network.network_address, network.network_address)
                max_addr = max(current_network.broadcast_address, network.broadcast_address)
                
                # 计算新的前缀长度
                new_prefix = 32
                for prefix in range(32, -1, -1):
                    try:
                        candidate = ipaddress.IPv4Network((min_addr, prefix), strict=False)
                        if (candidate.network_address == min_addr and 
                            candidate.broadcast_address >= max_addr):
                            new_prefix = prefix
                            break
                    except:
                        continue
                
                current_network = ipaddress.IPv4Network((min_addr, new_prefix), strict=False)
                changed = True  # 标记本轮有合并发生
            else:
                merged_networks.append(current_network)
                current_network = network
        
        merged_networks.append(current_network)
        sorted_networks = merged_networks  # 更新排序后的网段列表
    
    return [str(net) for net in sorted_networks]

#遍历json文件夹
def process_json_files_in_folder(folder_path, output_file):
    """
    遍历文件夹中的所有JSON文件，提取并合并ip_parent网段，保存结果到output_file
    
    参数:
        folder_path (str): 包含JSON文件的文件夹路径
        output_file (str): 输出结果的文件路径
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
                    print(ip_parents)
                    print(f"已处理文件: {filename}, 提取到 {len(ip_parents)} 个IP网段")
            except json.JSONDecodeError:
                print(f"错误: 文件 {filename} 不是有效的JSON格式，已跳过")
            except Exception as e:
                print(f"错误: 处理文件 {filename} 时发生异常 - {e}")
    
    # # 合并所有IP网段
    # merged_networks = merge_ipv4_networks(all_ip_parents)
    
    # # 将结果保存到输出文件
    # try:
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump({"merged_networks": merged_networks}, f, indent=2, ensure_ascii=False)
    #     print(f"合并完成，结果已保存到 {output_file}")
    # except Exception as e:
    #     print(f"错误: 保存结果到 {output_file} 时失败 - {e}")
    
    # 不合并所有IP网段
    merged_networks = all_ip_parents
    
    # 将结果保存到输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"merged_networks": merged_networks}, f, indent=2, ensure_ascii=False)
        print(f"合并完成，结果已保存到 {output_file}")
    except Exception as e:
        print(f"错误: 保存结果到 {output_file} 时失败 - {e}")



if __name__ == "__main__":
    folder_path = "/Users/xiehanqi.jackson/Documents/CODE/11-17/original_data/北京"
    output_file = "/Users/xiehanqi.jackson/Documents/CODE/11-17/黄村-2.json"
    
    if os.path.isdir(folder_path):
        process_json_files_in_folder(folder_path, output_file)
    else:
        print("错误: 指定的文件夹路径不存在！")
 