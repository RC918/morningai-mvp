"""
Two Factor Authentication Service Module

提供 2FA 功能的抽象層，支援 TOTP 和備份碼
"""

import os
import pyotp
import qrcode
import base64
import secrets
import hashlib
from io import BytesIO
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class TwoFactorServiceInterface(ABC):
    """2FA 服務介面"""
    
    @abstractmethod
    def generate_secret(self) -> str:
        """生成 2FA 密鑰"""
        pass
    
    @abstractmethod
    def generate_qr_code(self, secret: str, username: str, issuer: str = "MorningAI") -> str:
        """生成 QR code"""
        pass
    
    @abstractmethod
    def verify_otp(self, secret: str, otp_code: str) -> bool:
        """驗證 OTP 代碼"""
        pass
    
    @abstractmethod
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """生成備份碼"""
        pass
    
    @abstractmethod
    def hash_backup_code(self, code: str) -> str:
        """雜湊備份碼"""
        pass
    
    @abstractmethod
    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """驗證備份碼"""
        pass


class TwoFactorService(TwoFactorServiceInterface):
    """實際的 2FA 服務實作"""
    
    def generate_secret(self) -> str:
        """生成 32 字符的 Base32 密鑰"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, username: str, issuer: str = "MorningAI") -> str:
        """生成 QR code 並回傳 Base64 編碼的圖片"""
        try:
            # 生成 TOTP URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=username,
                issuer_name=issuer
            )
            
            # 生成 QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # 創建圖片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 轉換為 Base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"[2FA_SERVICE] Failed to generate QR code: {e}")
            return ""
    
    def verify_otp(self, secret: str, otp_code: str) -> bool:
        """驗證 OTP 代碼"""
        try:
            if not secret or not otp_code:
                return False
            
            totp = pyotp.TOTP(secret)
            return totp.verify(otp_code, valid_window=1)
            
        except Exception as e:
            print(f"[2FA_SERVICE] Failed to verify OTP: {e}")
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """生成備份碼"""
        codes = []
        for _ in range(count):
            # 生成 8 位數字備份碼
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """使用 SHA-256 雜湊備份碼"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """驗證備份碼"""
        return self.hash_backup_code(code) == hashed_code


class MockTwoFactorService(TwoFactorServiceInterface):
    """測試用的 Mock 2FA 服務"""
    
    def __init__(self):
        self.generated_secrets = []
        self.verified_otps = []
        self.generated_backup_codes = []
    
    def generate_secret(self) -> str:
        """Mock 生成密鑰"""
        secret = "JBSWY3DPEHPK3PXP"  # 固定的測試密鑰
        self.generated_secrets.append(secret)
        return secret
    
    def generate_qr_code(self, secret: str, username: str, issuer: str = "MorningAI") -> str:
        """Mock 生成 QR code"""
        return f"data:image/png;base64,mock_qr_code_for_{username}"
    
    def verify_otp(self, secret: str, otp_code: str) -> bool:
        """Mock 驗證 OTP"""
        self.verified_otps.append({'secret': secret, 'code': otp_code})
        # 測試用固定驗證邏輯
        return otp_code == "123456"
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Mock 生成備份碼"""
        codes = [f"1234567{i}" for i in range(count)]
        self.generated_backup_codes.extend(codes)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Mock 雜湊備份碼"""
        return f"hashed_{code}"
    
    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """Mock 驗證備份碼"""
        return hashed_code == f"hashed_{code}"


# 全域 2FA 服務實例
_two_factor_service = None


def get_two_factor_service() -> TwoFactorServiceInterface:
    """獲取 2FA 服務實例"""
    global _two_factor_service
    
    if _two_factor_service is None:
        # 根據環境變數決定使用哪種服務
        if os.environ.get('TESTING') == 'True':
            _two_factor_service = MockTwoFactorService()
        else:
            _two_factor_service = TwoFactorService()
    
    return _two_factor_service


def set_two_factor_service(service: TwoFactorServiceInterface):
    """設定 2FA 服務實例（主要用於測試）"""
    global _two_factor_service
    _two_factor_service = service
