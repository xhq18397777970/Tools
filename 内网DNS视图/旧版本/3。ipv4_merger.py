#!/usr/bin/env python3
"""
IPv4网段合并工具
基于cidr-merger的Go代码逻辑移植到Python
支持CIDR格式和IP范围的合并
"""

import ipaddress
from typing import List, Union, Tuple


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
    
    Args:
        networks: 待合并的网段列表，支持CIDR格式(如"192.168.1.0/24")或IP范围格式(如"192.168.1.1-192.168.1.254")
    
    Returns:
        合并后的网段列表，以CIDR格式返回
    
    示例:
        >>> merge_ipv4_networks(["192.168.1.0", "192.168.1.1", "192.168.1.2/31"])
        ['192.168.1.0/31', '192.168.1.2/32']
        
        >>> merge_ipv4_networks(["192.168.1.0-192.168.1.3", "192.168.1.4-192.168.1.7"])
        ['192.168.1.0/29']
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
        # 如果当前结束+1 >= 下一个开始，则可以合并
        current_end_plus_1 = current_end + 1
        if current_end_plus_1 >= next_start:
            # 扩展当前范围
            if next_end > current_end:
                current_end = next_end
        else:
            # 无法合并，保存当前范围并开始新范围
            merged_ranges.append((current_start, current_end))
            current_start, current_end = next_start, next_end
    
    # 添加最后一个范围
    merged_ranges.append((current_start, current_end))
    
    # 4. 将合并后的范围转换回CIDR格式
    result = []
    for start, end in merged_ranges:
        # 使用ipaddress的summarize_address_range将范围转换为CIDR列表
        cidr_list = list(ipaddress.summarize_address_range(start, end))
        result.extend([str(cidr) for cidr in cidr_list])
    
    return result


def main():
    """测试函数"""
    # 测试用例1: 基本合并
    test_networks1 = [
        "6.97.0.0/16",
        "6.96.0.0/16",
        "6.6.0.0/16",
        "6.19.0.0/16",
        "6.31.0.0/16",
        "6.40.0.0/16",
        "6.54.0.0/16",
        "6.58.0.0/16",
        "6.60.0.0/15",
        "6.62.0.0/16",
        "6.103.0.0/16",
        "6.104.0.0/15",
        "6.172.0.0/14",
        "6.177.32.0/19",
        "6.177.64.0/19",
        "6.255.255.12/30",
        "10.18.0.0/18",
        "10.18.80.0/20",
        "10.18.128.0/18",
        "10.18.192.0/19",
        "10.20.0.0/16",
        "10.164.64.0/18",
        "10.172.0.0/14",
        "10.180.0.0/15",
        "10.183.128.128/25",
        "10.188.0.0/14",
        "10.192.0.0/15",
        "10.194.0.0/16",
        "10.202.0.0/15",
        "11.26.0.0/15",
        "11.28.0.0/15",
        "11.46.0.0/15",
        "11.52.0.0/16",
        "11.55.0.0/16",
        "11.62.0.0/15",
        "11.64.0.0/16",
        "11.66.0.0/15",
        "11.95.0.0/16",
        "11.96.0.0/15",
        "11.98.0.0/16",
        "11.100.0.0/16",
        "11.102.0.0/16",
        "11.115.0.0/16",
        "11.116.0.0/16",
        "11.118.0.0/16",
        "11.120.0.0/16",
        "11.129.0.0/16",
        "11.130.0.0/15",
        "11.134.0.0/16",
        "11.143.0.0/16",
        "11.151.0.0/16",
        "11.154.0.0/15",
        "11.255.2.0/23",
        "172.17.216.0/21",
        "172.18.0.0/18",
        "172.18.128.0/18",
        "172.18.192.0/19",
        "172.20.0.0/15",
        "172.27.60.0/22"
    ]
    print("测试1 - 基本合并:")
    print(f"输入: {test_networks1}")
    result1 = merge_ipv4_networks(test_networks1)
    print("----------------输出: ")
    for i in result1:
        print(f'"{i}",')

    print()
    
    # # 测试用例2: IP范围合并
    # test_networks2 = ["192.168.1.0-192.168.1.3", "192.168.1.4-192.168.1.7", "192.168.1.8-192.168.1.15"]
    # print("测试2 - IP范围合并:")
    # print(f"输入: {test_networks2}")
    # result2 = merge_ipv4_networks(test_networks2)
    # print(f"输出: {result2}")
    # print()
    
    # # 测试用例3: 混合格式
    # test_networks3 = ["192.168.1.0/24", "192.168.2.0/25", "192.168.2.128-192.168.2.255"]
    # print("测试3 - 混合格式:")
    # print(f"输入: {test_networks3}")
    # result3 = merge_ipv4_networks(test_networks3)
    # print(f"输出: {result3}")
    # print()
    
    # # 测试用例4: 不重叠的网段
    # test_networks4 = ["192.168.1.0/24", "10.0.0.0/24", "172.16.0.0/24"]
    # print("测试4 - 不重叠网段:")
    # print(f"输入: {test_networks4}")
    # result4 = merge_ipv4_networks(test_networks4)
    # print(f"输出: {result4}")


if __name__ == "__main__":
    main()