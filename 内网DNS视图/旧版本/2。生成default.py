#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
需用python3运行；
直接编码中指定ACL文件夹路径和输出路径，输出剩余IP段到指定路径的default.acl文件；
'''

import ipaddress
import sys
import os
import glob

def read_exclude_nets_from_file(filename):
    exclude_nets = []
    in_acl_block = False
    with open(filename, 'r') as file:
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
                exclude_nets.append(ipaddress.ip_network(network_str, strict=False))
    return exclude_nets

def exclude_subnets_from_global(exclude_nets):
    global_net = ipaddress.ip_network('0.0.0.0/0')
    remaining_nets = [global_net]
    for exclude_net in exclude_nets:
        new_remaining = []
        for net in remaining_nets:
            if exclude_net.subnet_of(net):
                new_remaining.extend(list(net.address_exclude(exclude_net)))
            else:
                new_remaining.append(net)
        remaining_nets = new_remaining
    return remaining_nets

def write_to_default_acl(result, output_file):
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as file:
        file.write('acl "acl-default" {\n')
        for net in sorted(result, key=lambda x: int(x.network_address)):
            file.write("    {};\n".format(net))
        file.write('};\n')

def get_acl_files_from_directory(directory):
    """获取指定目录下除default.acl外的所有.acl文件"""
    pattern = os.path.join(directory, '*.acl')
    all_acl_files = glob.glob(pattern)
    return [f for f in all_acl_files
            if not os.path.basename(f).lower() == 'default.acl']

def main():
    # 直接在代码中指定参数
    input_dir = "/Users/xiehanqi.jackson/Documents/CODE/11-24/acl"  # 修改为你的ACL文件夹路径
    output_dir = "/Users/xiehanqi.jackson/Documents/CODE/11-24/acl"  # 修改为你的输出目录路径
    
    # 验证输入文件夹是否存在
    if not os.path.isdir(input_dir):
        print("错误: 输入文件夹不存在: {}".format(input_dir), file=sys.stderr)
        sys.exit(1)

    # 获取ACL文件列表（排除default.acl）
    acl_files = get_acl_files_from_directory(input_dir)
    
    if not acl_files:
        print("警告: 在文件夹 {} 中未找到任何.acl文件（除default.acl外）".format(input_dir), file=sys.stderr)
        sys.exit(0)

    # 设置输出文件路径
    output_file = os.path.join(output_dir, 'default.acl')

    # 读取所有排除网段
    all_exclude_nets = []
    for filename in acl_files:
        try:
            all_exclude_nets.extend(read_exclude_nets_from_file(filename))
            print("已处理文件: {}".format(os.path.basename(filename)))
        except Exception as e:
            print("警告: 无法处理文件 {}: {}".format(filename, e), file=sys.stderr)

    # 计算剩余网段并输出
    result = exclude_subnets_from_global(all_exclude_nets)
    write_to_default_acl(result, output_file)
    print("输入文件夹: {}".format(input_dir))
    print("输出文件: {}".format(output_file))
    print("处理文件数量: {}".format(len(acl_files)))
    print("剩余IP段数量: {}".format(len(result)))

if __name__ == '__main__':
    main()