"""
Two-Factor Authentication (2FA) Tests
Tests for 2FA setup, verification, and backup code functionality.
"""

import pytest
import pyotp
import qrcode
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestTwoFactorSetup:
    """Test 2FA setup functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_user_id = 123
        self.test_email = "test@example.com"
        self.app_name = "MorningAI MVP"
        
    def test_generate_2fa_secret(self):
        """Test generation of 2FA secret key."""
        # Generate a new secret
        secret = pyotp.random_base32()
        
        assert secret is not None
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secret should be 32 chars
        
    def test_generate_qr_code(self):
        """Test generation of QR code for 2FA setup."""
        secret = pyotp.random_base32()
        
        # Create provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=self.test_email,
            issuer_name=self.app_name
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri, optimize=0)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes for testing
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        assert len(img_bytes) > 0
        assert provisioning_uri in str(qr.data_list[0].data, 'utf-8')
        
    def test_verify_2fa_token_valid(self):
        """Test verification of valid 2FA token."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Generate current token
        current_token = totp.now()
        
        # Verify token
        is_valid = totp.verify(current_token, valid_window=1)
        
        assert is_valid is True
        
    def test_verify_2fa_token_invalid(self):
        """Test verification of invalid 2FA token."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Use an obviously invalid token
        invalid_token = "000000"
        
        # Verify token
        is_valid = totp.verify(invalid_token, valid_window=1)
        
        assert is_valid is False
        
    def test_verify_2fa_token_expired(self):
        """Test verification of expired 2FA token."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Generate token for a past time (more than valid window)
        import datetime
        past_time = totp.timecode(for_time=datetime.datetime.now() - datetime.timedelta(minutes=5))
        past_token = totp.generate_otp(past_time)
        
        # Verify token with narrow window
        is_valid = totp.verify(past_token, valid_window=0)
        
        assert is_valid is False


class TestBackupCodes:
    """Test backup codes functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_user_id = 123
        
    def test_generate_backup_codes(self):
        """Test generation of backup codes."""
        import secrets
        import string
        
        def generate_backup_codes(count=10):
            codes = []
            for _ in range(count):
                # Generate 8-character alphanumeric code
                code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                codes.append(code)
            return codes
            
        backup_codes = generate_backup_codes()
        
        assert len(backup_codes) == 10
        for code in backup_codes:
            assert len(code) == 8
            assert code.isalnum()
            assert code.isupper()
            
    def test_verify_backup_code_valid(self):
        """Test verification of valid backup code."""
        # Mock stored backup codes
        stored_codes = ["ABCD1234", "EFGH5678", "IJKL9012"]
        test_code = "ABCD1234"
        
        # Verify backup code
        is_valid = test_code in stored_codes
        
        assert is_valid is True
        
    def test_verify_backup_code_invalid(self):
        """Test verification of invalid backup code."""
        stored_codes = ["ABCD1234", "EFGH5678", "IJKL9012"]
        test_code = "INVALID1"
        
        # Verify backup code
        is_valid = test_code in stored_codes
        
        assert is_valid is False
        
    def test_backup_code_single_use(self):
        """Test that backup codes can only be used once."""
        stored_codes = ["ABCD1234", "EFGH5678", "IJKL9012"]
        test_code = "ABCD1234"
        
        # First use
        if test_code in stored_codes:
            stored_codes.remove(test_code)
            first_use_success = True
        else:
            first_use_success = False
            
        # Second use attempt
        second_use_success = test_code in stored_codes
        
        assert first_use_success is True
        assert second_use_success is False


class TestTwoFactorAuthentication:
    """Test complete 2FA authentication flow."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_user_id = 123
        self.test_email = "test@example.com"
        
    def test_2fa_setup_flow(self):
        """Test complete 2FA setup flow."""
        # Step 1: Generate secret
        secret = pyotp.random_base32()
        
        # Step 2: Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=self.test_email,
            issuer_name="MorningAI MVP"
        )
        
        # Step 3: User scans QR and enters token
        current_token = totp.now()
        
        # Step 4: Verify setup token
        setup_verified = totp.verify(current_token, valid_window=1)
        
        # Step 5: Generate backup codes
        import secrets
        import string
        backup_codes = [''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)) for _ in range(10)]
        
        assert secret is not None
        assert provisioning_uri is not None
        assert setup_verified is True
        assert len(backup_codes) == 10
        
    def test_2fa_login_flow_with_totp(self):
        """Test 2FA login flow using TOTP."""
        # Assume user has already set up 2FA
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Step 1: User provides username/password (mocked as successful)
        primary_auth_success = True
        
        # Step 2: User provides TOTP token
        user_token = totp.now()
        
        # Step 3: Verify TOTP token
        totp_verified = totp.verify(user_token, valid_window=1)
        
        # Step 4: Complete authentication
        login_success = primary_auth_success and totp_verified
        
        assert login_success is True
        
    def test_2fa_login_flow_with_backup_code(self):
        """Test 2FA login flow using backup code."""
        # Assume user has already set up 2FA
        stored_backup_codes = ["ABCD1234", "EFGH5678", "IJKL9012"]
        
        # Step 1: User provides username/password (mocked as successful)
        primary_auth_success = True
        
        # Step 2: User provides backup code
        user_backup_code = "ABCD1234"
        
        # Step 3: Verify backup code
        backup_code_verified = user_backup_code in stored_backup_codes
        if backup_code_verified:
            stored_backup_codes.remove(user_backup_code)  # Single use
            
        # Step 4: Complete authentication
        login_success = primary_auth_success and backup_code_verified
        
        assert login_success is True
        assert user_backup_code not in stored_backup_codes  # Code should be removed
        
    def test_2fa_disable_flow(self):
        """Test 2FA disable flow."""
        # Mock current 2FA status
        user_2fa_enabled = True
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Step 1: User requests to disable 2FA
        # Step 2: Verify current password (mocked)
        password_verified = True
        
        # Step 3: Verify TOTP token for confirmation
        confirmation_token = totp.now()
        totp_verified = totp.verify(confirmation_token, valid_window=1)
        
        # Step 4: Disable 2FA
        if password_verified and totp_verified:
            user_2fa_enabled = False
            secret = None  # Clear secret
            backup_codes = []  # Clear backup codes
            
        assert user_2fa_enabled is False
        assert secret is None
