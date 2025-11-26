#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import ipaddress
import os



def load_ip_networks(filename):
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
                ip_networks.append(ipaddress.ip_network(network_str, strict=False))
    return ip_networks

def ip_networks_overlap(network1, network2):
    return network1.overlaps(network2)

def check_for_overlaps(acl1_filename, acl2_filename):
    acl1_networks = load_ip_networks(acl1_filename)
    acl2_networks = load_ip_networks(acl2_filename)

    overlaps = []
    for network1 in acl1_networks:
        for network2 in acl2_networks:
            if ip_networks_overlap(network1, network2):
                overlaps.append((network1, network2))

    return overlaps

def compare_files(file1, file2):
    overlaps = check_for_overlaps(file1, file2)
    if overlaps:
        # 只显示文件名，不显示完整路径
        file1_name = os.path.basename(file1)
        file2_name = os.path.basename(file2)
        print(f"\n[{file1_name}] 和 [{file2_name}] 的有交集的IP范围如下：")
        for overlap in overlaps:
            print(f"{overlap[0]} 与 {overlap[1]} 有交集")

def main():
    # 获取ACL目录下所有.acl文件
    files = [os.path.join(ACL_DIR, f) for f in os.listdir(ACL_DIR)
            if os.path.isfile(os.path.join(ACL_DIR, f)) and f.endswith('.acl')]
    
    if not files:
        print(f"在目录 {ACL_DIR} 中没有找到任何.acl文件")
        return
    
    print(f"正在检查目录 {ACL_DIR} 下的 {len(files)} 个ACL文件...")
    
    # 比较所有文件对
    for i in range(len(files)):
        for j in range(i+1, len(files)):
            compare_files(files[i], files[j])

if __name__ == "__main__":
    # 硬编码的ACL目录路径
    ACL_DIR = '/Users/xiehanqi.jackson/Documents/CODE/11-26/acl'
    main()