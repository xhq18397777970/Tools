#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import hashlib
import time

def generate_auth_params():
    """
    生成鉴权所需的参数
    返回包含 Auth, Timestamp, User 的字典
    """
    timestamp = int(time.time())
    user = "api_np"
    token = "ddc4cbd6f13bb9186f4add38b23015d9"
    
    # 生成签名串
    sign_str = user + token + str(timestamp)
    
    # 计算MD5
    auth = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    return {
        "Auth": auth,
        "Timestamp": timestamp,
        "User": user
    }

def modify_check_api():
    # API地址
    url = "http://127.0.0.1:10025/check"
    
    # 生成鉴权参数
    auth_params = generate_auth_params()
    
    # 请求参数
    payload = {
        "gray_domain": "j1.com",
        "gray_swim_lane": "GRAY_RETAIL_MAIN",
        "gray_ups": "gray_retail_main"
    }
    
    # 合并字典（兼容Python 3.5以下版本）
    request_data = payload.copy()
    request_data.update(auth_params)
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(request_data)
        )
        
        # 检查响应状态码
        if response.status_code == 200:
            result = response.json()
            print("API调用成功:")
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
        else:
            print("API调用失败，状态码: {}".format(response.status_code))
            print("错误信息: {}".format(response.text))
            return None
            
    except requests.exceptions.RequestException as e:
        print("请求发生异常: {}".format(str(e)))
        return None
def delete_check_api():
        # API地址
    url = "http://127.0.0.1:10025/delete"
    
    # 生成鉴权参数
    auth_params = generate_auth_params()
    
    # 请求参数
    payload = {
        "gray_domain": "33",
    }
    
    # 合并字典（兼容Python 3.5以下版本）
    request_data = payload.copy()
    request_data.update(auth_params)
    
    try:
        # 发送POST请求
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(request_data)
        )
        
        # 检查响应状态码
        if response.status_code == 200:
            result = response.json()
            print("API调用成功:")
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
        else:
            print("API调用失败，状态码: {}".format(response.status_code))
            print("错误信息: {}".format(response.text))
            return None
            
    except requests.exceptions.RequestException as e:
        print("请求发生异常: {}".format(str(e)))
        return None
if __name__ == '__main__':
    modify_check_api()
