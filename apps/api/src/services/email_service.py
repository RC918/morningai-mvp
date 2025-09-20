"""
Email Service Module

提供郵件發送功能的抽象層，支援測試環境的 mock
"""

import os
from abc import ABC, abstractmethod
from typing import Optional


class EmailServiceInterface(ABC):
    """郵件服務介面"""

    @abstractmethod
    def send_verification_email(self, email: str, verification_link: str) -> bool:
        """發送驗證郵件"""
        pass

    @abstractmethod
    def send_password_reset_email(self, email: str, reset_link: str) -> bool:
        """發送密碼重設郵件"""
        pass


class EmailService(EmailServiceInterface):
    """實際的郵件服務實作"""

    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "localhost")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@morningai.com")

    def send_verification_email(self, email: str, verification_link: str) -> bool:
        """發送驗證郵件"""
        try:
            # 在實際環境中，這裡會使用 SMTP 發送郵件
            # 目前為了測試，我們只記錄日誌
            print(f"[EMAIL_SERVICE] Sending verification email to {email}")
            print(f"[EMAIL_SERVICE] Verification link: {verification_link}")

            # 模擬發送成功
            return True

        except Exception as e:
            print(f"[EMAIL_SERVICE] Failed to send verification email: {e}")
            return False

    def send_password_reset_email(self, email: str, reset_link: str) -> bool:
        """發送密碼重設郵件"""
        try:
            print(f"[EMAIL_SERVICE] Sending password reset email to {email}")
            print(f"[EMAIL_SERVICE] Reset link: {reset_link}")

            # 模擬發送成功
            return True

        except Exception as e:
            print(f"[EMAIL_SERVICE] Failed to send password reset email: {e}")
            return False


class MockEmailService(EmailServiceInterface):
    """測試用的 Mock 郵件服務"""

    def __init__(self):
        self.sent_emails = []

    def send_verification_email(self, email: str, verification_link: str) -> bool:
        """Mock 發送驗證郵件"""
        self.sent_emails.append(
            {"type": "verification", "email": email, "link": verification_link}
        )
        return True

    def send_password_reset_email(self, email: str, reset_link: str) -> bool:
        """Mock 發送密碼重設郵件"""
        self.sent_emails.append(
            {"type": "password_reset", "email": email, "link": reset_link}
        )
        return True

    def get_sent_emails(self):
        """獲取已發送的郵件記錄"""
        return self.sent_emails

    def clear_sent_emails(self):
        """清除已發送的郵件記錄"""
        self.sent_emails.clear()


# 全域郵件服務實例
_email_service = None


def get_email_service() -> EmailServiceInterface:
    """獲取郵件服務實例"""
    global _email_service

    if _email_service is None:
        # 根據環境變數決定使用哪種服務
        if os.environ.get("TESTING") == "True":
            _email_service = MockEmailService()
        else:
            _email_service = EmailService()

    return _email_service


def set_email_service(service: EmailServiceInterface):
    """設定郵件服務實例（主要用於測試）"""
    global _email_service
    _email_service = service


# 便利函數
def send_email(email: str, verification_link: str) -> bool:
    """發送驗證郵件的便利函數"""
    return get_email_service().send_verification_email(email, verification_link)
