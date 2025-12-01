import requests
import json
import time

# API基本配置
BASE_URL = "http://localhost:8000/api"
UPLOAD_URL = f"{BASE_URL}/documents/"
PROCESS_URL = f"{BASE_URL}/documents/{{document_id}}/process"
GET_DOCUMENT_URL = f"{BASE_URL}/documents/{{document_id}}"

# 认证信息 - 替换为实际的token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjkyNWE2ZmIwYTQ5Y2YyNzJhNjZjMWYxIiwidXNlcm5hbWUiOiJhZG1pbiIsImVtYWlsIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJleHAiOjE3NjQzODQwNzAsInJvbGUiOiJhZG1pbiJ9.f7Qj3Y6Z7X8W9E0R1T2Y3U4I5O6P7A8S9D0F1G2H3J4K5L6M7N8O9P0Q1R2S3T4U5V6W7X8Y9Z0"

# 测试文件路径
TEST_FILE_PATH = "c:\dailywork\graduation project\Lingtu_Zhipu\需求1.pdf"

def test_document_upload_and_process():
    """测试文档上传和处理功能"""
    print("开始测试文档上传和处理功能...")
    
    # 1. 上传文档
    print("\n1. 上传文档...")
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
    with open(TEST_FILE_PATH, "rb") as f:
        files = {
            "file": ("需求1.pdf", f, "application/pdf")
        }
        data = {
            "title": "测试文档",
            "description": "这是一个测试文档",
            "document_type": "pdf",
            "industry": "测试行业"
        }
        
        response = requests.post(UPLOAD_URL, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            document_data = response.json()
            document_id = document_data["id"]
            print(f"✅ 文档上传成功，文档ID: {document_id}")
        else:
            print(f"❌ 文档上传失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return
    
    # 2. 处理文档
    print(f"\n2. 处理文档 (ID: {document_id})...")
    process_url = PROCESS_URL.format(document_id=document_id)
    response = requests.post(process_url, headers=headers)
    
    if response.status_code == 200:
        print("✅ 文档处理任务已成功安排")
    else:
        print(f"❌ 文档处理任务安排失败，状态码: {response.status_code}")
        print(f"错误信息: {response.text}")
        return
    
    # 3. 轮询检查文档处理状态
    print("\n3. 检查文档处理状态...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"   第 {attempt} 次检查...")
        
        get_url = GET_DOCUMENT_URL.format(document_id=document_id)
        response = requests.get(get_url, headers=headers)
        
        if response.status_code == 200:
            document_data = response.json()
            status = document_data["status"]
            print(f"   当前状态: {status}")
            
            if status == "processed":
                print("✅ 文档处理成功！")
                print(f"   实体数量: {document_data.get('entities_count', 0)}")
                print(f"   关系数量: {document_data.get('relations_count', 0)}")
                return
            elif status == "failed":
                print("❌ 文档处理失败！")
                print(f"   错误信息: {document_data.get('processing_error', '未知错误')}")
                return
        else:
            print(f"   获取文档状态失败，状态码: {response.status_code}")
        
        # 等待2秒后再次检查
        time.sleep(2)
    
    print("❌ 文档处理超时，超过最大检查次数")

if __name__ == "__main__":
    test_document_upload_and_process()
