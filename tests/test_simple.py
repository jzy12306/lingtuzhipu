import requests
import json

# API端点
BASE_URL = "http://127.0.0.1:8000/api"

# 1. 登录获取token
def login():
    """登录获取token"""
    print("登录系统...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None
    
    return response.json().get("access_token")

# 2. 上传文档
def upload_document(token):
    """上传文档"""
    print("\n上传文档...")
    
    # 读取测试文件
    with open("测试文件.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": "测试文件",
        "description": "用于测试知识提取的文件",
        "document_type": "markdown",
        "filename": "测试文件.md",
        "content": content
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        print(f"文档上传失败: {response.status_code} - {response.text}")
        return None
    
    document = response.json()
    print(f"文档上传成功，ID: {document['id']}")
    return document['id']

# 3. 处理文档
def process_document(token, document_id):
    """处理文档"""
    print(f"\n处理文档 {document_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/process",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"文档处理请求失败: {response.status_code} - {response.text}")
        return False
    
    print("文档处理请求成功，开始异步处理")
    return True

# 4. 检查文档状态
def check_document_status(token, document_id):
    """检查文档状态"""
    print(f"\n检查文档 {document_id} 状态...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"获取文档状态失败: {response.status_code} - {response.text}")
        return None
    
    return response.json()

# 5. 获取提取的实体和关系
def get_extracted_knowledge(token, document_id):
    """获取提取的实体和关系"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 获取实体
    print("\n获取提取的实体...")
    entities_response = requests.get(
        f"{BASE_URL}/knowledge/entities?document_id={document_id}",
        headers=headers
    )
    
    if entities_response.status_code != 200:
        print(f"获取实体失败: {entities_response.status_code} - {entities_response.text}")
        entities = []
    else:
        entities = entities_response.json()
        print(f"提取到 {len(entities)} 个实体")
        for entity in entities:
            print(f"- {entity.get('name')} ({entity.get('type')})")
    
    # 获取关系
    print("\n获取提取的关系...")
    relations_response = requests.get(
        f"{BASE_URL}/knowledge/relations?document_id={document_id}",
        headers=headers
    )
    
    if relations_response.status_code != 200:
        print(f"获取关系失败: {relations_response.status_code} - {relations_response.text}")
        relations = []
    else:
        relations = relations_response.json()
        print(f"提取到 {len(relations)} 个关系")
        for relation in relations:
            print(f"- {relation.get('source_entity_name')} {relation.get('type')} {relation.get('target_entity_name')}")
    
    return entities, relations

# 主函数
def main():
    """主函数"""
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 上传文档
    document_id = upload_document(token)
    if not document_id:
        return
    
    # 3. 处理文档
    if not process_document(token, document_id):
        return
    
    # 4. 等待处理完成
    import time
    print("\n等待文档处理完成...")
    for i in range(30):
        time.sleep(1)
        doc_status = check_document_status(token, document_id)
        if doc_status:
            status = doc_status.get("status")
            print(f"文档状态: {status}")
            
            if status == "processed":
                print("\n文档处理完成！")
                print(f"提取的实体数: {doc_status.get('extracted_entities', 0)}")
                print(f"提取的关系数: {doc_status.get('extracted_relationships', 0)}")
                
                # 获取提取的实体和关系
                get_extracted_knowledge(token, document_id)
                return
            elif status == "failed":
                print(f"\n文档处理失败: {doc_status.get('processing_error')}")
                return
        
        print(f"等待中... ({i+1}/30秒)")
    
    print("\n文档处理超时")

if __name__ == "__main__":
    main()