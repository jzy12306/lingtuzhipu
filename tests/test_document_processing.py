import asyncio
import httpx
import json
import os

# 测试文件路径
TEST_FILE_PATH = "c:\dailywork\graduation project\Lingtu_Zhipu\测试文件.md"

# API端点
BASE_URL = "http://127.0.0.1:8000/api"
UPLOAD_URL = f"{BASE_URL}/documents/"
PROCESS_URL = f"{BASE_URL}/documents/{{document_id}}/process"

async def test_document_processing():
    """测试文档处理流程"""
    async with httpx.AsyncClient() as client:
        # 1. 读取测试文件内容
        print("读取测试文件...")
        with open(TEST_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"文件内容长度: {len(content)}字符")
        
        # 2. 登录获取token（使用默认管理员账户）
        print("\n登录系统...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"登录失败: {login_response.status_code} - {login_response.text}")
            return
        
        token = login_response.json().get("access_token")
        print(f"登录成功，获取到token: {token[:20]}...")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 3. 上传文档
        print("\n上传文档...")
        upload_response = await client.post(
            UPLOAD_URL,
            json={
                "title": "测试文件",
                "description": "用于测试知识提取的文件",
                "document_type": "markdown",
                "filename": "测试文件.md",
                "content": content
            },
            headers=headers
        )
        
        if upload_response.status_code != 200:
            print(f"文档上传失败: {upload_response.status_code} - {upload_response.text}")
            return
        
        document = upload_response.json()
        document_id = document.get("id")
        print(f"文档上传成功，文档ID: {document_id}")
        
        # 4. 处理文档
        print("\n处理文档...")
        process_response = await client.post(
            PROCESS_URL.format(document_id=document_id),
            headers=headers
        )
        
        if process_response.status_code != 200:
            print(f"文档处理请求失败: {process_response.status_code} - {process_response.text}")
            return
        
        print(f"文档处理请求成功，开始异步处理")
        
        # 5. 等待处理完成（模拟前端轮询）
        print("\n等待文档处理完成...")
        for i in range(30):  # 最多等待30秒
            await asyncio.sleep(1)
            
            # 获取文档状态
            status_response = await client.get(
                f"{BASE_URL}/documents/{document_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                doc_status = status_response.json()
                status = doc_status.get("status")
                print(f"文档状态: {status}")
                
                if status == "processed":
                    print("文档处理完成！")
                    print(f"提取的实体数: {doc_status.get('extracted_entities', 0)}")
                    print(f"提取的关系数: {doc_status.get('extracted_relationships', 0)}")
                    print(f"处理错误: {doc_status.get('processing_error')}")
                    
                    # 获取提取的实体
                    entities_response = await client.get(
                        f"{BASE_URL}/knowledge/entities?document_id={document_id}",
                        headers=headers
                    )
                    
                    if entities_response.status_code == 200:
                        entities = entities_response.json()
                        print(f"\n提取的实体列表 ({len(entities)}个):")
                        for entity in entities:
                            print(f"- {entity.get('name')} ({entity.get('type')})")
                    
                    # 获取提取的关系
                    relations_response = await client.get(
                        f"{BASE_URL}/knowledge/relations?document_id={document_id}",
                        headers=headers
                    )
                    
                    if relations_response.status_code == 200:
                        relations = relations_response.json()
                        print(f"\n提取的关系列表 ({len(relations)}个):")
                        for relation in relations:
                            print(f"- {relation.get('source_entity_name')} {relation.get('type')} {relation.get('target_entity_name')}")
                    
                    return
                elif status == "failed":
                    print(f"文档处理失败: {doc_status.get('processing_error')}")
                    return
            
            print(f"等待中... ({i+1}/30秒)")
        
        print("文档处理超时")

if __name__ == "__main__":
    asyncio.run(test_document_processing())