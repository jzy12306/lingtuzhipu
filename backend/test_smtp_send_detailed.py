import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import traceback

# 加载环境变量
load_dotenv()

# 获取SMTP配置
smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
smtp_port = int(os.getenv("SMTP_PORT", "465"))
sender_email = os.getenv("SENDER_EMAIL", "3058099144@qq.com")
sender_name = os.getenv("SENDER_NAME", "账户安全中心")
auth_code = os.getenv("QQ_EMAIL_AUTH_CODE", "")

# 测试邮件信息
to_email = "16627630187@163.com"  # 用户提供的网易邮箱
code = "123456"

print(f"\n=== 详细SMTP发送测试 ===")
print(f"SMTP服务器: {smtp_server}:{smtp_port}")
print(f"发件人: {sender_name} <{sender_email}>")
print(f"收件人: {to_email}")
print(f"验证码: {code}")

# 创建SSL上下文
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

try:
    # 连接SMTP服务器
    print("\n1. 连接SMTP服务器...")
    server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=15)
    server.set_debuglevel(2)  # 设置详细调试信息
    
    print("\n2. 发送EHLO命令...")
    ehlo_result = server.ehlo()
    print(f"EHLO结果: {ehlo_result}")
    
    print("\n3. 登录SMTP服务器...")
    login_result = server.login(sender_email, auth_code)
    print(f"登录结果: {login_result}")
    
    # 创建简单邮件（纯文本）
    print("\n4. 创建邮件...")
    subject = f"【账户验证】您的验证码是：{code}"
    body = f"验证码：{code}（5分钟内有效）"
    
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Reply-To"] = sender_email
    
    print("\n5. 发送邮件...")
    send_result = server.sendmail(sender_email, to_email, msg.as_string())
    print(f"发送结果: {send_result}")
    
    if send_result:
        print(f"\n❌ 发送失败，未送达邮箱: {send_result}")
    else:
        print(f"\n✅ 发送成功！")
    
    print("\n6. 退出SMTP服务器...")
    quit_result = server.quit()
    print(f"退出结果: {quit_result}")
    
except Exception as e:
    print(f"\n❌ 发送失败: {str(e)}")
    print(f"错误类型: {type(e).__name__}")
    print(f"详细错误信息:")
    traceback.print_exc()
