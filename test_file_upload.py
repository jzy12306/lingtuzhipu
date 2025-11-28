import requests
import os

# 测试文件上传功能

def test_file_upload():
    # 1. 登录获取token
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "email": "admin@example.com",
        "password": "admin123456"
    }
    
    print("1. 正在登录...")
    login_response = requests.post(login_url, json=login_data)
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return False
    
    login_result = login_response.json()
    token = login_result.get("access_token")
    print(f"登录成功，获取到token: {token[:20]}...")
    
    # 2. 使用用户提供的PDF文件
    test_file_path = "c:/dailywork/graduation project/Lingtu_Zhipu/需求1.pdf"
    
    # 3. 上传文件
    upload_url = "http://localhost:8000/api/documents/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(test_file_path, "rb") as f:
        files = {
            "file": f
        }
        
        print("\n2. 正在上传文件...")
        upload_response = requests.post(upload_url, headers=headers, files=files)
        print(f"上传状态码: {upload_response.status_code}")
        print(f"上传响应: {upload_response.text}")
    
    # 4. 注意：不清理用户提供的真实PDF文件
    
    # 5. 验证上传结果
    if upload_response.status_code != 200:
        print(f"\n❌ 文件上传失败: {upload_response.status_code} {upload_response.text}")
        return False
    
    # 6. 获取文档ID并测试处理功能
    upload_result = upload_response.json()
    document_id = upload_result.get("id")
    print(f"\n3. 正在测试文档处理功能，文档ID: {document_id}")
    
    process_url = f"http://localhost:8000/api/documents/{document_id}/process"
    process_response = requests.post(process_url, headers=headers)
    print(f"处理请求状态码: {process_response.status_code}")
    print(f"处理响应: {process_response.text}")
    
    # 7. 验证最终结果
    if process_response.status_code == 200:
        print("\n✅ 文件上传和处理功能都成功！修复完全生效。")
        return True
    else:
        print(f"\n⚠️  文件上传成功，但处理失败: {process_response.status_code} {process_response.text}")
        print("   请检查后端日志获取详细错误信息")
        return False

if __name__ == "__main__":
    test_file_upload()