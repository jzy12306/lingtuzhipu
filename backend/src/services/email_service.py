import smtplib
import os
import time
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Lock
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# 邮件服务配置
SMTP_CONFIG = {
    "server": os.getenv("SMTP_SERVER", "smtp.qq.com"),
    "port": int(os.getenv("SMTP_PORT", "465")),
    "sender_email": os.getenv("SENDER_EMAIL", "3058099144@qq.com"),
    "sender_name": os.getenv("SENDER_NAME", "账户安全中心"),
    "auth_code": os.getenv("QQ_EMAIL_AUTH_CODE", ""),  # 从环境变量获取
    "use_ssl": True
}

# 验证码模板
EMAIL_TEMPLATES = {
    "verification": {
        "subject": "【账户验证】您的验证码是：{code}",
        "html_body": """
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
    },
    "password_reset": {
        "subject": "【密码重置】您的验证码是：{code}",
        "html_body": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>密码重置</h2>
            <p>您正在重置账户密码，验证码为：</p>
            <div style="background: #f5f5f5; padding: 15px; text-align: center; font-size: 24px; letter-spacing: 5px; margin: 20px 0;">
                <strong>{code}</strong>
            </div>
            <p>验证码5分钟内有效。如非本人操作，请忽略此邮件。</p>
            <p>此邮件由系统自动发送，请勿回复。</p>
        </div>
        """
    },
    "security_alert": {
        "subject": "【安全提醒】您的账户有重要操作",
        "html_body": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>安全提醒</h2>
            <p>您的账户正在进行重要操作，请确认是否为您本人操作。</p>
            <p>如非本人操作，请立即修改密码并联系客服。</p>
            <p>此邮件由系统自动发送，请勿回复。</p>
        </div>
        """
    }
}

# 频率限制器 (内存缓存)
rate_limiter: Dict[str, List[float]] = {}
rate_lock = Lock()
MAX_REQUESTS_PER_5MIN = 3  # 5分钟内最多3次请求
MAX_REQUESTS_PER_24H = 10  # 24小时内最多10次请求
TIME_WINDOW_5MIN = 300  # 5分钟窗口
TIME_WINDOW_24H = 86400  # 24小时窗口


class EmailService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config = SMTP_CONFIG
        self._initialized = True

    def _get_smtp_connection(self):
        """获取SMTP连接 (带连接池)"""
        context = ssl.create_default_context()
        return smtplib.SMTP_SSL(
            self.config["server"], 
            self.config["port"], 
            context=context
        )

    def _check_rate_limit(self, email: str) -> Tuple[bool, float]:
        """检查发送频率限制"""
        with rate_lock:
            now = time.time()
            if email not in rate_limiter:
                rate_limiter[email] = []
            
            # 清理过期记录
            rate_limiter[email] = [t for t in rate_limiter[email] 
                                 if now - t < TIME_WINDOW_24H]
            
            # 检查24小时限制
            if len(rate_limiter[email]) >= MAX_REQUESTS_PER_24H:
                wait_time = TIME_WINDOW_24H - (now - rate_limiter[email][0])
                return False, wait_time
            
            # 检查5分钟限制
            recent_requests = [t for t in rate_limiter[email] 
                             if now - t < TIME_WINDOW_5MIN]
            if len(recent_requests) >= MAX_REQUESTS_PER_5MIN:
                wait_time = TIME_WINDOW_5MIN - (now - recent_requests[0])
                return False, wait_time
            
            rate_limiter[email].append(now)
            return True, 0.0

    def send_verification_code(self, to_email: str, code: str, purpose: str = "verification") -> bool:
        """发送验证码"""
        # 1. 频率检查
        allowed, wait_time = self._check_rate_limit(to_email)
        if not allowed:
            raise Exception(f"请求过于频繁，请{int(wait_time)}秒后再试")
        
        # 2. 构建邮件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = EMAIL_TEMPLATES[purpose]["subject"].format(code=code)
        msg["From"] = f"{self.config['sender_name']} <{self.config['sender_email']}>"
        msg["To"] = to_email
        
        # HTML和纯文本版本
        html_part = MIMEText(EMAIL_TEMPLATES[purpose]["html_body"].format(code=code), "html")
        text_part = MIMEText(f"验证码：{code}（5分钟内有效）", "plain")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # 3. 发送邮件
        try:
            with self._get_smtp_connection() as server:
                server.login(self.config["sender_email"], self.config["auth_code"])
                server.sendmail(
                    self.config["sender_email"],
                    to_email,
                    msg.as_string()
                )
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            raise Exception("验证码发送失败，请稍后重试")

    def send_security_alert(self, to_email: str, alert_message: str) -> bool:
        """发送安全提醒"""
        # 构建邮件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = EMAIL_TEMPLATES["security_alert"]["subject"]
        msg["From"] = f"{self.config['sender_name']} <{self.config['sender_email']}>"
        msg["To"] = to_email
        
        # HTML和纯文本版本
        html_body = EMAIL_TEMPLATES["security_alert"]["html_body"]
        html_part = MIMEText(html_body, "html")
        text_part = MIMEText("安全提醒：您的账户正在进行重要操作，请确认是否为您本人操作。", "plain")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # 发送邮件
        try:
            with self._get_smtp_connection() as server:
                server.login(self.config["sender_email"], self.config["auth_code"])
                server.sendmail(
                    self.config["sender_email"],
                    to_email,
                    msg.as_string()
                )
            return True
        except Exception as e:
            logger.error(f"安全提醒邮件发送失败: {str(e)}")
            return False


# 创建全局邮件服务实例
email_service = EmailService()