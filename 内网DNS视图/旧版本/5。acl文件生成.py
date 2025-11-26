# import json
# import os
 
# def convert_json_to_acl(json_file_path: str, acl_file_path: str):
#     """
#     将包含网络列表的 JSON 文件转换为指定的 ACL 格式。
 
#     Args:
#         json_file_path (str): 输入的 JSON 文件路径。
#         acl_file_path (str): 输出的 ACL 文件路径。
#     """
#     # 1. 读取并解析 JSON 文件
#     try:
#         with open(json_file_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
#     except FileNotFoundError:
#         print(f"错误: 文件未找到于路径 '{json_file_path}'")
#         return
#     except json.JSONDecodeError:
#         print(f"错误: 文件 '{json_file_path}' 不是有效的 JSON 格式。")
#         return
 
#     # 2. 从数据中提取网络列表
#     # 使用 .get() 方法可以避免因键不存在而引发的 KeyError，如果键不存在则返回一个空列表
#     networks = data.get('merged_networks', [])
 
#     # 3. 构建 ACL 文件的内容字符串
#     # 使用列表推导式和 join 方法高效地格式化每一行网络地址
#     network_lines = "\n".join([f"  {net};" for net in networks])
#     acl_content = f"""acl "acl-" {{{network_lines}}};"""
 
#     # 4. 将生成的内容写入 ACL 文件
#     try:
#         with open(acl_file_path, 'w', encoding='utf-8') as f:
#             f.write(acl_content)
#         print(f"转换成功: '{json_file_path}' -> '{acl_file_path}'")
#     except IOError as e:
#         print(f"错误: 无法写入文件 '{acl_file_path}'。原因: {e}")
 
# if __name__ == "__main__":
#     # -------------------------------------------------------------------------
#     # 在此区域硬编码您的文件路径
#     # -------------------------------------------------------------------------
 
#     # 输入的 JSON 文件名（或完整路径）
#     input_json_file = '/Users/xiehanqi.jackson/Documents/CODE/11-19-3/廊坊/其他.json'
    
#     # 希望生成的 ACL 文件名（或完整路径）
#     output_acl_file = '/Users/xiehanqi.jackson/Documents/CODE/11-19-3/acl/lf-1.acl'
 
#     # -------------------------------------------------------------------------
#     # 执行转换
#     # -------------------------------------------------------------------------
 
#     convert_json_to_acl(input_json_file, output_acl_file)

import json
import os
 
def convert_json_to_acl(json_file_path: str, acl_file_path: str):
    """
    将包含网络列表的 JSON 文件转换为指定的 ACL 格式。
    (此函数是核心转换逻辑，保持不变)
 
    Args:
        json_file_path (str): 输入的 JSON 文件路径。
        acl_file_path (str): 输出的 ACL 文件路径。
    """
    # 1. 读取并解析 JSON 文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"警告: 文件未找到于路径 '{json_file_path}' (跳过)")
        return
    except json.JSONDecodeError:
        print(f"错误: 文件 '{json_file_path}' 不是有效的 JSON 格式。(跳过)")
        return
 
    # 2. 从数据中提取网络列表
    # 使用 .get() 方法可以避免因键不存在而引发的 KeyError，如果键不存在则返回一个空列表
    networks = data.get('merged_networks', [])
 
    if not networks:
        print(f"信息: 文件 '{json_file_path}' 中未找到 'merged_networks' 或列表为空，将生成空的 ACL 文件。")
 
    # 3. 构建 ACL 文件的内容字符串
    # 使用列表推导式和 join 方法高效地格式化每一行网络地址
    network_lines = "\n".join([f"  {net};" for net in networks])
    acl_content = f"""acl "acl-" {{{network_lines}}};"""
 
    # 4. 将生成的内容写入 ACL 文件
    try:
        with open(acl_file_path, 'w', encoding='utf-8') as f:
            f.write(acl_content)
        print(f"转换成功: '{os.path.basename(json_file_path)}' -> '{os.path.basename(acl_file_path)}'")
    except IOError as e:
        print(f"错误: 无法写入文件 '{acl_file_path}'。原因: {e}")
 
 
def convert_all_jsons_in_folder(input_folder: str, output_folder: str):
    """
    批量转换一个文件夹内的所有 JSON 文件为 ACL 文件。
 
    Args:
        input_folder (str): 包含源 JSON 文件的文件夹路径。
        output_folder (str): 用于存放生成的 ACL 文件的文件夹路径。
    """
    # 1. 检查输入文件夹是否存在
    if not os.path.isdir(input_folder):
        print(f"错误: 输入文件夹 '{input_folder}' 不存在或不是一个有效的目录。")
        return
 
    # 2. 确保输出文件夹存在，如果不存在则创建它
    os.makedirs(output_folder, exist_ok=True)
    print(f"输出目录已准备就绪: '{output_folder}'")
 
    # 3. 遍历输入文件夹中的所有文件
    print(f"开始扫描输入文件夹: '{input_folder}'")
    for filename in os.listdir(input_folder):
        # 4. 检查文件是否是 .json 文件
        if filename.lower().endswith('.json'):
            # 构建完整的输入文件路径和输出文件路径
            input_file_path = os.path.join(input_folder, filename)
            
            # 创建同名的 .acl 文件
            output_filename = os.path.splitext(filename)[0] + '.acl'
            output_file_path = os.path.join(output_folder, output_filename)
            
            print("-" * 20)
            print(f"正在处理文件: {filename}")
            
            # 调用核心转换函数
            convert_json_to_acl(input_file_path, output_file_path)
        else:
            print(f"跳过非 JSON 文件: {filename}")
 
    print("-" * 20)
    print("所有文件处理完毕。")
 
 
if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # 在此区域配置您的文件夹路径
    # -------------------------------------------------------------------------
 
    # 输入的 JSON 文件所在文件夹的路径
    # 示例: '/Users/xiehanqi.jackson/Documents/CODE/11-19-3/廊坊'
    input_json_folder = '/Users/xiehanqi.jackson/Documents/CODE/11-26/json_results'
    
    # 希望生成的 ACL 文件存放的文件夹路径
    # 示例: '/Users/xiehanqi.jackson/Documents/CODE/11-19-3/acl'
    output_acl_folder = '/Users/xiehanqi.jackson/Documents/CODE/11-26/acl'
 
    # -------------------------------------------------------------------------
    # 执行批量转换
    # -------------------------------------------------------------------------
 
    convert_all_jsons_in_folder(input_json_folder, output_acl_folder)