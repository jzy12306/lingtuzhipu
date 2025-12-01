import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from src.services.db_service import db_service
import asyncio

async def check_docs():
    db = await db_service.get_mongodb()
    if db:
        docs = await db.documents.find({'status': 'knowledge_extracting'}).to_list(10)
        print(f'Found {len(docs)} docs with status knowledge_extracting: {[d.get("id") for d in docs]}')
        
        # Also check for any docs with invalid statuses
        all_docs = await db.documents.find().to_list(20)
        print(f'\nChecking status of all docs:')
        for doc in all_docs:
            print(f'Doc {doc.get("id")}: status = {doc.get("status")}')

if __name__ == '__main__':
    asyncio.run(check_docs())