import requests
import json
import time
import hashlib
import os

def network_req(dirctory_name, param, value):
    # 1. 使用 Python 计算 Auth
    def generate_auth():
        timestamp = int(time.time())
        user = "api_np"
        token = "ddc4cbd6f13bb9186f4add38b23015d9"
        
        sign_str = user + token + str(timestamp)
        # 使用 hashlib 进行 MD5 加密
        auth = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        return {
            "Auth": auth,
            "Timestamp": timestamp,
            "User": user
        }

    # 2. 调用函数获取认证参数
    auth_params = generate_auth()
    auth = auth_params["Auth"]
    user = auth_params["User"]
    timestamp = auth_params["Timestamp"]

    # 3. 请求参数
    url = f"http://openapi.smartops.jd.com/cabinetSpace/v2/instances/query/segment_pool?user={user}&auth={auth}&timestamp={timestamp}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json;charset=utf-8"
    }

    # 4. 分页获取数据并保存
    start = 1
    limit = 2000  # 每页最大2000条
    total_data = []  # 存储所有数据
    file_index = 1  # 文件序号

    
    # 确保输出目录存在
    os.makedirs(dirctory_name, exist_ok=True)

    while True:
        payload = {
        "page": {
            "start": start,
            "limit": limit
        },
        "conditions": {
            "rules": [
                {
                    "field": param,
                    "operator": "in",
                    "value": 
                        value
                    
                }
            ]
        }
    }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()  # 解析JSON响应

            # 假设返回的数据在 data.result 或类似字段中（根据实际API调整）
            if "result" in data:
                batch_data = data["result"]
            else:
                batch_data = data  # 如果没有嵌套，直接使用
            pages=int(int(batch_data['data']['total'])/2000)
            
            if len(batch_data["data"]["list"])==0:  # 如果返回空数据，说明没有更多数据了
                print("数据获取完毕没有更多数据")
                break

            print("【共",pages+1,"页】【当前采集第",start,"页】")
            # 保存当前批次数据到文件
            output_file = f"{dirctory_name}/page_{file_index}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(batch_data, f, ensure_ascii=False, indent=2)
            print(f"        保存文件路径: {output_file}")

            # 更新分页和文件序号
            start += 1
            file_index += 1

            # 控制请求速度（避免过快）
            time.sleep(2)  # 暂停1秒

        except requests.exceptions.RequestException as e:
            print("请求失败:", e)
            break  # 如果请求失败，退出循环

    print("所有数据获取完成！")


def logic_name_convert_list(logic_list):
    # 一行代码版本
    try:
        with open(logic_list, "r", encoding="utf-8") as f:
            
            list = [line.strip() for line in f if line.strip()]
            print(list)
            return list
            
    except:
        print("文件读取失败")
        
def batch_execute_from_json(config_file):
    """
    从JSON配置文件批量执行任务
    
    Args:
        config_file: JSON配置文件路径，包含多个任务的配置
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        print(f"从配置文件 {config_file} 加载了 {len(configs)} 个任务")
        
        for i, config in enumerate(configs, 1):
            print(f"\n{'='*50}")
            print(f"执行第 {i} 个任务")
            print(f"{'='*50}")
            
            # 获取配置参数
            dir_name = config.get('dir')
            logic_list = config.get('logic_list')
            param = "logic_name"  # 固定参数
            
            if not dir_name or not logic_list:
                print(f"❌ 任务 {i} 配置不完整: dir={dir_name}, logic_list={logic_list}")
                continue
                
            print(f"目录: {dir_name}")
            print(f"逻辑列表: {logic_list}")
            
            # 执行任务
            network_req(dir_name, param, logic_list)
            
        print(f"\n所有任务执行完成！")
        
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_file}")
    except json.JSONDecodeError:
        print(f"❌ 配置文件格式错误: {config_file}")
    except Exception as e:
        print(f"❌ 执行批量任务时出错: {e}")

# 使用示例
if __name__ == "__main__":
    # 从JSON配置文件批量执行
    config_file = "/Users/xiehanqi.jackson/Documents/CODE/逻辑机房.json"  # 修改为您的配置文件路径
    batch_execute_from_json(config_file)