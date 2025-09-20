import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.main import app
from src.database import db
from src.models.user import User
from src.models.jwt_blacklist import JWTBlacklist
from src.models.audit_log import AuditLog, AuditActions

@pytest.fixture
def client():
    """測試客戶端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()  # 確保清空所有表
            db.create_all()
            
            # 創建測試用戶
            test_user = User(
                username='testuser',
                email='test@example.com',
                role='user',
                is_active=True,
                is_email_verified=False
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            
            # 創建管理員用戶
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                is_active=True,
                is_email_verified=True
            )
            admin_user.set_password('password123')
            db.session.add(admin_user)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Database setup error: {e}")
            
        yield client
        
        # 清理
        with app.app_context():
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    """獲取認證標頭"""
    # 登入獲取 token
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    token = data['token']
    
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_headers(client):
    """獲取管理員認證標頭"""
    response = client.post('/api/login', json={
        'email': 'admin@example.com',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    token = data['token']
    
    return {'Authorization': f'Bearer {token}'}

class TestEmailVerification:
    """Email 驗證模組測試"""
    
    def test_send_verification_email(self, client, auth_headers):
        """測試發送驗證郵件"""
        with patch("src.services.email_service.send_email") as mock_send:
            mock_send.return_value = True
            response = client.post("/api/auth/send-verification", headers=auth_headers)
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'Verification email sent' in data['message']
            mock_send.assert_called_once()
    
    def test_verify_email_with_valid_token(self, client):
        """測試有效 token 的郵件驗證"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # 生成驗證 token
            from itsdangerous import URLSafeTimedSerializer
            serializer = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'])
            token = serializer.dumps(user.email, salt='email-confirm')
            
            response = client.get(f'/api/auth/verify/{token}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'Email verified successfully' in data['message']
    
    def test_verify_email_with_invalid_token(self, client):
        """測試無效 token 的郵件驗證"""
        response = client.get('/api/auth/verify/invalid-token')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid verification token' in data['message']
    
    def test_get_email_verification_status(self, client, auth_headers):
        """測試獲取郵箱驗證狀態"""
        response = client.get('/api/auth/email-status', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'is_verified' in data
        assert data['is_verified'] is False

class TestJWTBlacklist:
    """JWT 黑名單模組測試"""
    
    def test_logout_adds_token_to_blacklist(self, client, auth_headers):
        """測試登出將 token 加入黑名單"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '登出成功' in data['message']
        
        # 驗證 token 已被加入黑名單
        with app.app_context():
            blacklist_count = JWTBlacklist.query.count()
            assert blacklist_count > 0
    
    def test_blacklisted_token_rejected(self, client, auth_headers):
        """測試黑名單中的 token 被拒絕"""
        # 先登出（將 token 加入黑名單）
        client.post('/api/auth/logout', headers=auth_headers)
        
        # 嘗試使用已被加入黑名單的 token
        response = client.get('/api/auth/email-status', headers=auth_headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Token has been revoked' in data['error']
    
    def test_logout_all_devices(self, client, auth_headers):
        """測試登出所有設備"""
        response = client.post('/api/auth/logout-all', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '已登出所有設備' in data['message']
    
    def test_admin_get_blacklist(self, client, admin_headers):
        """測試管理員獲取黑名單"""
        response = client.get('/api/admin/blacklist', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'blacklist' in data
        assert 'total' in data
    
    def test_non_admin_cannot_access_blacklist(self, client, auth_headers):
        """測試非管理員無法訪問黑名單"""
        response = client.get('/api/admin/blacklist', headers=auth_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'forbidden' in data['error']

class TestTwoFactorAuth:
    """2FA 模組測試"""
    
    def test_setup_2fa(self, client, auth_headers):
        """測試設置 2FA"""
        response = client.post('/api/auth/2fa/setup', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '2FA 設置成功' in data['message']
        assert 'secret' in data
        assert 'qr_code' in data
    
    def test_enable_2fa_with_valid_otp(self, client, auth_headers):
        """測試使用有效 OTP 啟用 2FA"""
        # 先設置 2FA
        setup_response = client.post('/api/auth/2fa/setup', headers=auth_headers)
        assert setup_response.status_code == 200
        
        # 從設置回應中獲取 secret
        setup_data = json.loads(setup_response.data)
        secret = setup_data['secret']
        
        # 生成有效的 OTP
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_otp = totp.now()
        
        response = client.post('/api/auth/2fa/enable', 
                             json={'otp': valid_otp},
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '2FA 已成功啟用' in data['message']
    
    def test_enable_2fa_with_invalid_otp(self, client, auth_headers):
        """測試使用無效 OTP 啟用 2FA"""
        # 先設置 2FA
        client.post('/api/auth/2fa/setup', headers=auth_headers)
        
        response = client.post('/api/auth/2fa/enable', 
                             json={'otp': '000000'},
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'OTP 驗證碼錯誤' in data['message']
    
    def test_get_2fa_status(self, client, auth_headers):
        """測試獲取 2FA 狀態"""
        response = client.get('/api/auth/2fa/status', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'two_factor_enabled' in data
        assert 'has_secret' in data
    
    def test_generate_backup_codes(self, client, auth_headers):
        """測試生成備用碼"""
        # 先設置並啟用 2FA
        setup_response = client.post('/api/auth/2fa/setup', headers=auth_headers)
        assert setup_response.status_code == 200
        
        # 從設置回應中獲取 secret
        setup_data = json.loads(setup_response.data)
        secret = setup_data['secret']
        
        # 啟用 2FA
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_otp = totp.now()
        
        enable_response = client.post('/api/auth/2fa/enable', 
                                    json={'otp': valid_otp},
                                    headers=auth_headers)
        assert enable_response.status_code == 200
        
        # 生成備份碼
        response = client.get('/api/auth/2fa/backup-codes',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'backup_codes' in data
        assert len(data['backup_codes']) == 10

class TestAuditLogging:
    """審計日誌模組測試"""
    
    def test_audit_log_creation(self, client):
        """測試審計日誌創建"""
        with app.app_context():
            log_entry = AuditLog.log_action(
                action=AuditActions.LOGIN,
                user_id=1,
                details={'test': 'data'},
                ip_address='127.0.0.1',
                status='success'
            )
            
            assert log_entry is not None
            assert log_entry.action == AuditActions.LOGIN
            assert log_entry.user_id == 1
            assert log_entry.status == 'success'
    
    def test_get_my_audit_logs(self, client, auth_headers):
        """測試獲取個人審計日誌"""
        response = client.get('/api/audit-logs/my', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'logs' in data
        assert 'total' in data
    
    def test_admin_get_audit_logs(self, client, admin_headers):
        """測試管理員獲取審計日誌"""
        response = client.get('/api/admin/audit-logs', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'logs' in data
        assert 'total' in data
    
    def test_non_admin_cannot_access_admin_logs(self, client, auth_headers):
        """測試非管理員無法訪問管理員日誌"""
        response = client.get('/api/admin/audit-logs', headers=auth_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'forbidden' in data['error']
    
    def test_audit_log_stats(self, client, admin_headers):
        """測試審計日誌統計"""
        response = client.get('/api/admin/audit-logs/stats', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_logs' in data
        assert 'failed_logs' in data
        assert 'success_rate' in data
    
    def test_audit_log_export(self, client, admin_headers):
        """測試審計日誌導出"""
        response = client.post('/api/admin/audit-logs/export',
                             json={'format': 'json'},
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '導出成功' in data['message']
        assert 'logs' in data
    
    def test_audit_log_cleanup(self, client, admin_headers):
        """測試審計日誌清理"""
        response = client.post('/api/admin/audit-logs/cleanup',
                             json={'days': 30},
                             headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cleaned_count' in data

class TestIntegration:
    """整合測試"""
    
    def test_login_creates_audit_log(self, client):
        """測試登入創建審計日誌"""
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        
        # 檢查是否創建了審計日誌
        with app.app_context():
            log_count = AuditLog.query.filter_by(action=AuditActions.LOGIN).count()
            assert log_count > 0
    
    def test_failed_login_creates_audit_log(self, client):
        """測試登入失敗創建審計日誌"""
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        
        # 檢查是否創建了失敗的審計日誌
        with app.app_context():
            log_count = AuditLog.query.filter_by(
                action=AuditActions.LOGIN_FAILED
            ).count()
            assert log_count > 0
    
    def test_jwt_with_jti_in_payload(self, client):
        """測試 JWT 包含 JTI"""
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data['token']
        
        # 解碼 token 檢查 JTI
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        assert 'jti' in payload
        assert payload['jti'] is not None
    
    def test_health_endpoint(self, client):
        """測試健康檢查端點"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'API is healthy' in data['message']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

