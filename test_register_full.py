import requests
import json
import time

# 测试完整的注册流程
def test_full_register():
    base_url = "http://localhost:8000/api/auth"
    headers = {"Content-Type": "application/json"}
    
    # 测试数据
    test_email = "test@example.com"
    test_username = "testuser"
    test_password = "Test1234"
    
    try:
        # 1. 发送验证码
        print("1. 发送验证码...")
        send_code_url = f"{base_url}/send-verification-code"
        send_code_data = {
            "email": test_email,
            "purpose": "register"
        }
        
        send_code_response = requests.post(send_code_url, headers=headers, data=json.dumps(send_code_data))
        print(f"发送验证码状态码: {send_code_response.status_code}")
        print(f"发送验证码响应: {send_code_response.text}")
        
        if send_code_response.status_code != 200:
            print("发送验证码失败！")
            return
        
        # 2. 等待1秒，然后使用固定验证码进行注册（实际应该从邮箱获取，但测试环境简化处理）
        print("\n2. 等待1秒后进行注册...")
        time.sleep(1)
        
        register_url = f"{base_url}/register"
        register_data = {
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "verification_code": "123456"  # 注意：实际环境中应该使用从邮箱收到的验证码
        }
        
        register_response = requests.post(register_url, headers=headers, data=json.dumps(register_data))
        print(f"注册状态码: {register_response.status_code}")
        print(f"注册响应: {register_response.text}")
        
        if register_response.status_code == 200:
            print("注册成功！")
        else:
            print("注册失败！")
            # 尝试解析错误信息
            try:
                error_data = register_response.json()
                print(f"错误详情: {error_data}")
            except:
                print("无法解析错误信息")
    
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_register()