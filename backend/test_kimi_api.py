import asyncio
import httpx
from src.config.settings import settings

async def test_kimi_api():
    """测试远程Kimi API是否可用"""
    print("=== 测试远程Kimi API ===")
    
    # 检查Kimi API配置
    if not settings.API_KEY:
        print("❌ Kimi API密钥未配置")
        return False
    
    print(f"✅ Kimi API配置：")
    print(f"   API_KEY: {settings.API_KEY[:10]}...")
    print(f"   API_BASE: {settings.API_BASE}")
    print(f"   MODEL: {settings.MODEL}")
    
    # 测试Kimi API调用
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个测试助手，只需要返回'测试成功'即可"},
                        {"role": "user", "content": "请返回'测试成功'"}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.0
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"].strip()
                if "测试成功" in content:
                    print("✅ Kimi API调用成功！")
                    print(f"   响应内容：{content}")
                    return True
                else:
                    print(f"❌ Kimi API返回内容不符合预期：{content}")
                    return False
            else:
                print(f"❌ Kimi API返回格式错误：{result}")
                return False
                
    except httpx.HTTPStatusError as e:
        print(f"❌ Kimi API请求失败，状态码：{e.response.status_code}")
        print(f"   响应内容：{e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Kimi API调用异常：{str(e)}")
        return False

async def test_local_llm():
    """测试本地LLM是否可用"""
    print("\n=== 测试本地LLM支持 ===")
    
    # 检查本地LLM配置
    print(f"✅ 本地LLM配置：")
    print(f"   LOCAL_LLM_ENABLED: {settings.LOCAL_LLM_ENABLED}")
    print(f"   LOCAL_LLM_URL: {settings.LOCAL_LLM_URL}")
    print(f"   LOCAL_LLM_MODEL: {settings.LOCAL_LLM_MODEL}")
    
    # 测试本地LLM调用
    try:
        async with httpx.AsyncClient(timeout=settings.LOCAL_LLM_TIMEOUT) as client:
            response = await client.post(
                f"{settings.LOCAL_LLM_URL}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.LOCAL_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "你是一个测试助手，只需要返回'测试成功'即可"},
                        {"role": "user", "content": "请返回'测试成功'"}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.0
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"].strip()
                print("✅ 本地LLM调用成功！")
                print(f"   响应内容：{content}")
                return True
            else:
                print(f"❌ 本地LLM返回格式错误：{result}")
                return False
                
    except httpx.HTTPStatusError as e:
        print(f"❌ 本地LLM请求失败，状态码：{e.response.status_code}")
        print(f"   响应内容：{e.response.text}")
        return False
    except Exception as e:
        print(f"❌ 本地LLM调用异常：{str(e)}")
        print("   本地LLM服务可能未运行或配置错误")
        return False

async def main():
    """主测试函数"""
    print("开始验证LLM解决方案...\n")
    
    # 测试远程Kimi API
    kimi_result = await test_kimi_api()
    
    # 测试本地LLM
    local_result = await test_local_llm()
    
    print("\n=== 测试结果总结 ===")
    print(f"远程Kimi API：{'✅ 可用' if kimi_result else '❌ 不可用'}")
    print(f"本地LLM支持：{'✅ 可用' if local_result else '❌ 不可用'}")
    
    if kimi_result or local_result:
        print("\n🎉 至少有一种LLM解决方案可用！")
    else:
        print("\n❌ 所有LLM解决方案均不可用，请检查配置")

if __name__ == "__main__":
    asyncio.run(main())
