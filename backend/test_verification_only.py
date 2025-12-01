import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.auth_service import auth_service
from src.services.db_service import db_service

async def test_verification_only():
    """
    仅测试验证码验证逻辑，不实际发送邮件
    """
    print("=== 验证码验证逻辑测试 ===")
    
    # 测试邮箱
    test_email = "test_verification@example.com"
    
    try:
        # 1. 获取数据库连接
        mongodb = await db_service.get_mongodb()
        if mongodb is None:
            print("❌ 数据库连接失败")
            return False
        
        # 清理测试数据
        await mongodb.verification_codes.delete_many({"email": test_email})
        
        print("\n1. 模拟发送验证码")
        # 手动插入验证码到数据库，模拟发送过程
        test_code = "123456"
        verification_code = {
            "email": test_email,
            "code": test_code,
            "purpose": "register",
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "created_at": datetime.utcnow(),
            "attempts": 0,
            "is_valid": True,
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent"
        }
        
        result = await mongodb.verification_codes.insert_one(verification_code)
        if result.inserted_id:
            print(f"✅ 验证码已模拟发送，生成的验证码: {test_code}")
        else:
            print("❌ 模拟发送验证码失败")
            return False
        
        # 2. 正确验证码测试
        print("\n2. 正确验证码验证测试")
        result = await auth_service.verify_verification_code(test_email, test_code, "register")
        if result:
            print("✅ 正确验证码验证成功")
        else:
            print("❌ 正确验证码验证失败")
            return False
        
        # 验证验证码已被标记为无效
        used_code = await mongodb.verification_codes.find_one({"_id": verification_code["_id"]})
        if used_code is not None and not used_code["is_valid"]:
            print("✅ 验证码已被正确标记为无效")
        else:
            print("❌ 验证码未被标记为无效")
            return False
        
        # 3. 重新插入验证码，测试错误验证码
        print("\n3. 错误验证码验证测试")
        new_verification_code = {
            "email": test_email,
            "code": test_code,
            "purpose": "register",
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "created_at": datetime.utcnow(),
            "attempts": 0,
            "is_valid": True,
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent"
        }
        new_result = await mongodb.verification_codes.insert_one(new_verification_code)
        if not new_result.inserted_id:
            print("❌ 重新插入验证码失败")
            return False
        
        wrong_code = "543210"
        result = await auth_service.verify_verification_code(test_email, wrong_code, "register")
        if not result:
            print("✅ 错误验证码验证失败（符合预期）")
        else:
            print("❌ 错误验证码验证成功（不符合预期）")
            return False
        
        # 4. 测试错误次数限制
        print("\n4. 错误次数限制测试")
        # 再尝试2次错误验证码，总共3次
        for i in range(2):
            result = await auth_service.verify_verification_code(test_email, wrong_code, "register")
            if not result:
                print(f"   ✅ 第{i+2}次错误验证码验证失败")
            else:
                print(f"   ❌ 第{i+2}次错误验证码验证成功（不符合预期）")
                return False
        
        # 验证验证码已被标记为无效
        invalid_code = await mongodb.verification_codes.find_one({"_id": new_verification_code["_id"]})
        if invalid_code is not None and not invalid_code["is_valid"]:
            print("✅ 错误次数达到限制，验证码已被标记为无效")
        else:
            print("❌ 错误次数达到限制，验证码未被标记为无效")
            return False
        
        # 5. 测试验证码过期
        print("\n5. 验证码过期测试")
        expire_verification_code = {
            "email": test_email,
            "code": test_code,
            "purpose": "register",
            "expires_at": datetime.utcnow() - timedelta(minutes=1),  # 设置为已过期
            "created_at": datetime.utcnow() - timedelta(minutes=6),
            "attempts": 0,
            "is_valid": True,
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent"
        }
        expire_result = await mongodb.verification_codes.insert_one(expire_verification_code)
        if not expire_result.inserted_id:
            print("❌ 插入过期验证码失败")
            return False
        
        result = await auth_service.verify_verification_code(test_email, test_code, "register")
        if not result:
            print("✅ 过期验证码验证失败（符合预期）")
        else:
            print("❌ 过期验证码验证成功（不符合预期）")
            return False
        
        print("\n=== 所有验证码验证逻辑测试通过！ ===")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据
        mongodb = await db_service.get_mongodb()
        if mongodb is not None:
            await mongodb.verification_codes.delete_many({"email": test_email})

if __name__ == "__main__":
    asyncio.run(test_verification_only())
