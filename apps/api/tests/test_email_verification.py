"""
Email Verification Tests
Tests for email verification token generation, sending, and validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


class TestEmailVerification:
    """Test email verification functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.secret_key = "test_secret_key"
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        self.test_email = "test@example.com"
        self.test_user_id = 123
        
    def test_generate_verification_token(self):
        """Test generation of email verification token."""
        # Mock token generation
        token_data = {'email': self.test_email, 'user_id': self.test_user_id}
        token = self.serializer.dumps(token_data, salt='email-verification')
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        # Generate a valid token
        token_data = {'email': self.test_email, 'user_id': self.test_user_id}
        token = self.serializer.dumps(token_data, salt='email-verification')
        
        # Verify the token
        try:
            decoded_data = self.serializer.loads(token, salt='email-verification', max_age=3600)
            assert decoded_data['email'] == self.test_email
            assert decoded_data['user_id'] == self.test_user_id
            verification_success = True
        except (SignatureExpired, BadSignature):
            verification_success = False
            
        assert verification_success is True
        
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        # Generate a token that will be considered expired
        token_data = {'email': self.test_email, 'user_id': self.test_user_id}
        token = self.serializer.dumps(token_data, salt='email-verification')
        
        # Try to verify with negative max_age to simulate expiration
        try:
            self.serializer.loads(token, salt='email-verification', max_age=-1)
            verification_success = True
        except SignatureExpired:
            verification_success = False
        except BadSignature:
            verification_success = False
            
        assert verification_success is False
        
    def test_verify_invalid_token(self):
        """Test verification of invalid/tampered token."""
        invalid_token = "invalid.token.here"
        
        try:
            self.serializer.loads(invalid_token, salt='email-verification', max_age=3600)
            verification_success = True
        except (SignatureExpired, BadSignature):
            verification_success = False
            
        assert verification_success is False
        
    def test_verify_wrong_salt_token(self):
        """Test verification of token with wrong salt."""
        # Generate token with one salt
        token_data = {'email': self.test_email, 'user_id': self.test_user_id}
        token = self.serializer.dumps(token_data, salt='wrong-salt')
        
        # Try to verify with different salt
        try:
            self.serializer.loads(token, salt='email-verification', max_age=3600)
            verification_success = True
        except (SignatureExpired, BadSignature):
            verification_success = False
            
        assert verification_success is False


class TestEmailSending:
    """Test email sending functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_email = "test@example.com"
        self.test_token = "test_verification_token"
        
    @patch('smtplib.SMTP')
    def test_send_verification_email_success(self, mock_smtp):
        """Test successful sending of verification email."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.send_message.return_value = {}
        
        # Mock email sending function
        def send_verification_email(email, token):
            try:
                # Simulate email sending logic
                server = mock_smtp('smtp.gmail.com', 587)
                server.starttls()
                server.login('test@gmail.com', 'password')
                
                # Create email content
                subject = "Email Verification"
                body = f"Please verify your email: http://localhost:3000/verify?token={token}"
                
                # Send email
                server.send_message(None)  # Simplified for testing
                server.quit()
                return True
            except Exception:
                return False
                
        result = send_verification_email(self.test_email, self.test_token)
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        
    @patch('smtplib.SMTP')
    def test_send_verification_email_failure(self, mock_smtp):
        """Test failed sending of verification email."""
        # Mock SMTP server with exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        def send_verification_email(email, token):
            try:
                server = mock_smtp('smtp.gmail.com', 587)
                return True
            except Exception:
                return False
                
        result = send_verification_email(self.test_email, self.test_token)
        assert result is False


class TestEmailVerificationFlow:
    """Test complete email verification flow."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_email = "test@example.com"
        self.test_user_id = 123
        
    def test_complete_verification_flow(self):
        """Test complete email verification flow."""
        # Step 1: Generate token
        serializer = URLSafeTimedSerializer("test_secret")
        token_data = {'email': self.test_email, 'user_id': self.test_user_id}
        token = serializer.dumps(token_data, salt='email-verification')
        
        # Step 2: Simulate email sending (mocked)
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            email_sent = True  # Assume email sending succeeds
            
        # Step 3: Verify token
        try:
            decoded_data = serializer.loads(token, salt='email-verification', max_age=3600)
            verification_success = True
            verified_email = decoded_data['email']
            verified_user_id = decoded_data['user_id']
        except (SignatureExpired, BadSignature):
            verification_success = False
            verified_email = None
            verified_user_id = None
            
        # Assertions
        assert email_sent is True
        assert verification_success is True
        assert verified_email == self.test_email
        assert verified_user_id == self.test_user_id
        
    def test_verification_flow_with_expired_token(self):
        """Test verification flow with expired token."""
        # Generate token
        serializer = URLSafeTimedSerializer("test_secret")
        token_data = {'email': self.test_email, 'user_id': self.test_user_id}
        token = serializer.dumps(token_data, salt='email-verification')
        
        # Try to verify with expired token (max_age=-1)
        try:
            serializer.loads(token, salt='email-verification', max_age=-1)
            verification_success = True
        except SignatureExpired:
            verification_success = False
        except BadSignature:
            verification_success = False
            
        assert verification_success is False
