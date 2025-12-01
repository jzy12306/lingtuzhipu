import smtplib
import ssl
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取SMTP配置
smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
smtp_port = int(os.getenv("SMTP_PORT", "465"))
sender_email = os.getenv("SENDER_EMAIL", "3058099144@qq.com")
auth_code = os.getenv("QQ_EMAIL_AUTH_CODE", "")

print(f"测试SMTP连接: {smtp_server}:{smtp_port}")
print(f"发件人邮箱: {sender_email}")
print(f"认证码: {'已配置' if auth_code else '未配置'}")

try:
    # 创建SSL上下文
    context = ssl.create_default_context()
    
    # 测试连接
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10) as server:
        print("\n连接成功！")
        
        # 测试登录
        try:
            server.login(sender_email, auth_code)
            print("登录成功！")
        except smtplib.SMTPAuthenticationError:
            print("登录失败：认证信息错误")
        except Exception as e:
            print(f"登录失败：{str(e)}")
            
except smtplib.SMTPConnectError as e:
    print(f"连接失败：无法连接到SMTP服务器 - {str(e)}")
except ssl.SSLError as e:
    print(f"SSL错误：{str(e)}")
except TimeoutError:
    print("连接超时：SMTP服务器无响应")
except Exception as e:
    print(f"连接失败：{str(e)}")
    print(f"错误类型：{type(e).__name__}")
