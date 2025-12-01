import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.auth_service import auth_service
from src.services.db_service import db_service

async def test_verification_code_flow():
    """
    测试验证码完整流程
    """
    print("=== 验证码验证流程测试 ===")
    
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
        
        print("\n1. 发送验证码测试")
        try:
            await auth_service.send_verification_code(test_email, "register")
            print("✅ 验证码发送成功")
        except Exception as e:
            print(f"❌ 验证码发送失败: {str(e)}")
            return False
        
        # 2. 查询生成的验证码
        verification_code = await mongodb.verification_codes.find_one({"email": test_email, "purpose": "register"})
        if verification_code is None:
            print("❌ 验证码未找到")
            return False
        
        real_code = verification_code["code"]
        print(f"   生成的验证码: {real_code}")
        
        # 3. 正确验证码测试
        print("\n2. 正确验证码验证测试")
        result = await auth_service.verify_verification_code(test_email, real_code, "register")
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
        
        # 4. 重新发送验证码，测试错误验证码
        print("\n3. 错误验证码验证测试")
        await auth_service.send_verification_code(test_email, "register")
        new_code = await mongodb.verification_codes.find_one({"email": test_email, "purpose": "register", "is_valid": True})
        if new_code is None:
            print("❌ 新验证码未找到")
            return False
        
        wrong_code = "543210"
        result = await auth_service.verify_verification_code(test_email, wrong_code, "register")
        if not result:
            print("✅ 错误验证码验证失败（符合预期）")
        else:
            print("❌ 错误验证码验证成功（不符合预期）")
            return False
        
        # 5. 测试错误次数限制
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
        invalid_code = await mongodb.verification_codes.find_one({"_id": new_code["_id"]})
        if invalid_code is not None and not invalid_code["is_valid"]:
            print("✅ 错误次数达到限制，验证码已被标记为无效")
        else:
            print("❌ 错误次数达到限制，验证码未被标记为无效")
            return False
        
        # 6. 测试验证码过期
        print("\n5. 验证码过期测试")
        await auth_service.send_verification_code(test_email, "register")
        expire_code = await mongodb.verification_codes.find_one({"email": test_email, "purpose": "register", "is_valid": True})
        if expire_code is None:
            print("❌ 过期测试验证码未找到")
            return False
        
        # 修改验证码过期时间为过去时间
        await mongodb.verification_codes.update_one(
            {"_id": expire_code["_id"]},
            {"$set": {"expires_at": datetime.utcnow() - timedelta(minutes=1)}}
        )
        
        result = await auth_service.verify_verification_code(test_email, expire_code["code"], "register")
        if not result:
            print("✅ 过期验证码验证失败（符合预期）")
        else:
            print("❌ 过期验证码验证成功（不符合预期）")
            return False
        
        print("\n=== 所有测试通过！验证码验证机制正常工作 ===")
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
    asyncio.run(test_verification_code_flow())
