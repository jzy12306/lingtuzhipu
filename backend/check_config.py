from src.services.db_service import db_service
import asyncio

async def check_config():
    await db_service.initialize()
    mongodb = await db_service.get_mongodb()
    config = await mongodb.system_config.find_one({})
    print('配置存在:', config is not None)
    if config:
        print('配置内容:', config)

asyncio.run(check_config())
