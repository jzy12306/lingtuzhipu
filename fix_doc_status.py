from pymongo import MongoClient
import datetime

# 直接连接MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['knowledge_graph']
documents_collection = db['documents']

# 查找状态为'knowledge_extracting'的文档
print("查找状态为'knowledge_extracting'的文档...")
docs = list(documents_collection.find({'status': 'knowledge_extracting'}))
print(f"找到 {len(docs)} 个文档，状态为'knowledge_extracting'")

# 修复这些文档的状态
for doc in docs:
    doc_id = doc['id']
    print(f"修复文档 {doc_id} 的状态...")
    
    # 更新文档状态为'processed'，并记录错误信息
    result = documents_collection.update_one(
        {'id': doc_id},
        {
            '$set': {
                'status': 'processed',
                'knowledge_extracted': False,
                'processing_error': '修复了无效的文档状态: knowledge_extracting',
                'updated_at': datetime.datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"成功修复文档 {doc_id}")
    else:
        print(f"修复文档 {doc_id} 失败")

# 检查所有文档的状态
print("\n检查所有文档的状态:")
all_docs = list(documents_collection.find().limit(10))
for doc in all_docs:
    print(f"文档 {doc['id']}: 状态 = {doc['status']}")

# 关闭连接
client.close()
print("\n修复完成！")