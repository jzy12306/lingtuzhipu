import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

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

print(f"\n测试发送邮件到: {to_email}")
print(f"验证码: {code}")

try:
    # 创建邮件
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【账户验证】您的验证码是：{code}"
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    
    # HTML和纯文本版本
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>账户验证</h2>
        <p>您正在注册/登录账户，验证码为：</p>
        <div style="background: #f5f5f5; padding: 15px; text-align: center; font-size: 24px; letter-spacing: 5px; margin: 20px 0;">
            <strong>{code}</strong>
        </div>
        <p>验证码5分钟内有效。如非本人操作，请忽略此邮件。</p>
        <p>此邮件由系统自动发送，请勿回复。</p>
    </div>
    """
    
    text_part = MIMEText(f"验证码：{code}（5分钟内有效）", "plain")
    html_part = MIMEText(html_body, "html")
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    # 创建SSL上下文
    context = ssl.create_default_context()
    
    # 发送邮件
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10) as server:
        server.login(sender_email, auth_code)
        server.sendmail(sender_email, to_email, msg.as_string())
    
    print("\n邮件发送成功！")
    print(f"验证码 {code} 已发送到 {to_email}")
    
except Exception as e:
    print(f"\n邮件发送失败：{str(e)}")
    print(f"错误类型：{type(e).__name__}")
