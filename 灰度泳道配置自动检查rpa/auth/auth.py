# -*- coding: utf-8 -*-
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
    sign_str = user+token+str(timestamp)
    
    # 计算MD5 (Python内置hashlib，不需要依赖CryptoJS)
    auth = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    return {
        "Auth": auth,
        "Timestamp": timestamp,
        "User": user
    }

def validate_auth_params(auth_params):
    """
    验证鉴权参数是否有效
    :param auth_params: 包含Auth, Timestamp, User的字典
    :return: bool 是否验证通过
    """
    if not all(key in auth_params for key in ["Auth", "Timestamp", "User"]):
        return False
    
    # 检查用户是否正确
    if auth_params.get("User") != "api_np":
        return False
    
    # 检查时间戳是否在有效期内（例如5分钟内）
    current_time = int(time.time())
    if abs(current_time - int(auth_params.get("Timestamp", 0))) > 300:  # 300秒=5分钟
        return False
    
    # 重新计算签名验证
    token = "ddc4cbd6f13bb9186f4add38b23015d9"
    sign_str = "{}{}{}".format(auth_params['User'],token,auth_params['Timestamp'])
    expected_auth = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    return auth_params.get("Auth") == expected_auth