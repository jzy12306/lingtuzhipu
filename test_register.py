import requests
import json

# 测试注册API
def test_register():
    url = "http://localhost:8000/api/auth/register"
    headers = {"Content-Type": "application/json"}
    
    # 测试数据
    test_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test1234",
        "verification_code": "123456"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(test_data))
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("注册成功！")
        else:
            print("注册失败！")
    except Exception as e:
        print(f"请求失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_register()