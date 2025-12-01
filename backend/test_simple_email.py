import smtplib
import ssl
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取SMTP配置
smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
smtp_port = int(os.getenv("SMTP_PORT", "465"))
sender_email = os.getenv("SENDER_EMAIL", "3058099144@qq.com")
auth_code = os.getenv("QQ_EMAIL_AUTH_CODE", "")

# 测试邮件信息
to_email = "16627630187@163.com"
code = "123456"

print(f"\n=== 简单邮件发送测试 ===")
print(f"SMTP服务器: {smtp_server}:{smtp_port}")
print(f"发件人: {sender_email}")
print(f"收件人: {to_email}")

# 创建简单纯文本邮件
msg = MIMEText(f"验证码：{code}（5分钟内有效）", "plain", "utf-8")
msg["From"] = sender_email
msg["To"] = to_email
msg["Subject"] = "账户验证验证码"

# 创建SSL上下文
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

try:
    # 连接并发送
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=15) as server:
        server.login(sender_email, auth_code)
        server.sendmail(sender_email, to_email, msg.as_string())
    print("\n✅ 邮件发送成功！")
    print(f"验证码 {code} 已发送到 {to_email}")
except Exception as e:
    print(f"\n❌ 发送失败: {str(e)}")
    import traceback
    traceback.print_exc()
