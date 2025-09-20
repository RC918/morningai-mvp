"""
全面測試覆蓋率提升測試套件
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import jwt

from src.main import app
from src.database import db
from src.models.user import User
from src.models.tenant import Tenant
from src.models.audit_log import AuditLog
from src.models.jwt_blacklist import JWTBlacklist
from src.models.webhook import Webhook
from src.services.email_service import EmailService
from src.services.two_factor_service import TwoFactorService


@pytest.fixture
def client():
    """測試客戶端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SUPABASE_URL'] = 'https://test.supabase.co'
    app.config['SUPABASE_SERVICE_ROLE_KEY'] = 'test-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # 創建測試租戶
            test_tenant = Tenant(
                name='Test Tenant',
                slug='test-tenant',
                domain='test.com',
                is_active=True
            )
            db.session.add(test_tenant)
            db.session.flush()
            
            # 創建測試用戶
            test_user = User(
                username='testuser',
                email='test@example.com',
                role='user',
                is_active=True,
                is_email_verified=True,
                tenant_id=test_tenant.id
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            
            # 創建管理員用戶
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                is_active=True,
                is_email_verified=True,
                tenant_id=test_tenant.id
            )
            admin_user.set_password('password123')
            db.session.add(admin_user)
            
            db.session.commit()
            
            yield client


def generate_token(user_id, role='user', exp_minutes=30):
    """生成測試 JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(minutes=exp_minutes),
        'jti': f'test-jti-{user_id}'
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')


class TestUserModel:
    """用戶模型測試"""
    
    def test_user_creation(self, client):
        """測試用戶創建"""
        with app.app_context():
            user = User(
                username='newuser',
                email='new@example.com',
                role='user'
            )
            user.set_password('password123')
            
            assert user.username == 'newuser'
            assert user.email == 'new@example.com'
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_user_repr(self, client):
        """測試用戶字符串表示"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert 'testuser' in repr(user)
    
    def test_user_to_dict(self, client):
        """測試用戶字典轉換"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            user_dict = user.to_dict()
            
            assert user_dict['username'] == 'testuser'
            assert user_dict['email'] == 'test@example.com'
            assert 'password_hash' not in user_dict


class TestTenantModel:
    """租戶模型測試"""
    
    def test_tenant_creation(self, client):
        """測試租戶創建"""
        with app.app_context():
            tenant = Tenant(
                name='New Tenant',
                slug='new-tenant',
                domain='new.com',
                is_active=True
            )
            db.session.add(tenant)
            db.session.commit()
            
            assert tenant.name == 'New Tenant'
            assert tenant.domain == 'new.com'
            assert tenant.is_active is True
    
    def test_tenant_users_relationship(self, client):
        """測試租戶用戶關係"""
        with app.app_context():
            tenant = Tenant.query.first()
            users = tenant.users
            
            assert len(users) >= 2  # 至少有測試用戶和管理員


class TestAuditLogModel:
    """審計日誌模型測試"""
    
    def test_audit_log_creation(self, client):
        """測試審計日誌創建"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            audit_log = AuditLog(
                user_id=user.id,
                action='test_action',
                resource_type='user',
                resource_id=user.id,
                details=json.dumps({'test': 'data'})
            )
            db.session.add(audit_log)
            db.session.commit()
            
            assert audit_log.action == 'test_action'
            assert audit_log.resource_type == 'user'
            assert audit_log.details == {'test': 'data'}
    
    def test_audit_log_to_dict(self, client):
        """測試審計日誌字典轉換"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            audit_log = AuditLog(
                user_id=user.id,
                action='test_action',
                resource_type='user',
                resource_id=user.id
            )
            db.session.add(audit_log)
            db.session.commit()
            
            log_dict = audit_log.to_dict()
            assert log_dict['action'] == 'test_action'
            assert log_dict['resource_type'] == 'user'


class TestJWTBlacklistModel:
    """JWT 黑名單模型測試"""
    
    def test_jwt_blacklist_creation(self, client):
        """測試 JWT 黑名單創建"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            blacklist_entry = JWTBlacklist(
                jti='test-jti-123',
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(blacklist_entry)
            db.session.commit()
            
            assert blacklist_entry.jti == 'test-jti-123'
            assert blacklist_entry.user_id == user.id
    
    def test_is_blacklisted(self, client):
        """測試黑名單檢查"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # 添加到黑名單
            blacklist_entry = JWTBlacklist(
                jti='test-jti-456',
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(blacklist_entry)
            db.session.commit()
            
            assert JWTBlacklist.is_blacklisted('test-jti-456') is True
            assert JWTBlacklist.is_blacklisted('non-existent-jti') is False
    
    def test_cleanup_expired(self, client):
        """測試清理過期黑名單"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # 添加過期的黑名單條目
            expired_entry = JWTBlacklist(
                jti='expired-jti',
                user_id=user.id,
                expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.session.add(expired_entry)
            db.session.commit()
            
            # 清理過期條目
            cleaned_count = JWTBlacklist.cleanup_expired()
            
            assert cleaned_count >= 1
            assert JWTBlacklist.is_blacklisted('expired-jti') is False


class TestWebhookModel:
    """Webhook 模型測試"""
    
    def test_webhook_creation(self, client):
        """測試 Webhook 創建"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            webhook = Webhook(
                user_id=user.id,
                url='https://example.com/webhook',
                event_type='user.created',
                is_active=True
            )
            db.session.add(webhook)
            db.session.commit()
            
            assert webhook.url == 'https://example.com/webhook'
            assert webhook.event_type == 'user.created'
            assert webhook.is_active is True
    
    def test_webhook_to_dict(self, client):
        """測試 Webhook 字典轉換"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            webhook = Webhook(
                user_id=user.id,
                url='https://example.com/webhook',
                event_type='user.created'
            )
            db.session.add(webhook)
            db.session.commit()
            
            webhook_dict = webhook.to_dict()
            assert webhook_dict['url'] == 'https://example.com/webhook'
            assert webhook_dict['event_type'] == 'user.created'


class TestEmailService:
    """郵件服務測試"""
    
    @patch('src.services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, client):
        """測試發送郵件成功"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_service = EmailService()
        result = email_service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()
    
    @patch('src.services.email_service.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp, client):
        """測試發送郵件失敗"""
        mock_smtp.side_effect = Exception('SMTP Error')
        
        email_service = EmailService()
        result = email_service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        assert result is False
    
    @patch('src.services.email_service.EmailService.send_email')
    def test_send_verification_email(self, mock_send, client):
        """測試發送驗證郵件"""
        mock_send.return_value = True
        
        email_service = EmailService()
        result = email_service.send_verification_email(
            'test@example.com',
            'verification-token'
        )
        
        assert result is True
        mock_send.assert_called_once()


class TestTwoFactorService:
    """雙重認證服務測試"""
    
    def test_generate_secret(self, client):
        """測試生成密鑰"""
        service = TwoFactorService()
        secret = service.generate_secret()
        
        assert isinstance(secret, str)
        assert len(secret) > 0
    
    def test_generate_qr_code(self, client):
        """測試生成 QR 碼"""
        service = TwoFactorService()
        secret = service.generate_secret()
        qr_code = service.generate_qr_code('test@example.com', secret)
        
        assert isinstance(qr_code, str)
        assert 'data:image/png;base64,' in qr_code
    
    def test_verify_token_valid(self, client):
        """測試驗證有效 token"""
        service = TwoFactorService()
        secret = service.generate_secret()
        
        # 生成當前時間的 token
        import pyotp
        totp = pyotp.TOTP(secret)
        current_token = totp.now()
        
        assert service.verify_token(secret, current_token) is True
    
    def test_verify_token_invalid(self, client):
        """測試驗證無效 token"""
        service = TwoFactorService()
        secret = service.generate_secret()
        
        assert service.verify_token(secret, '000000') is False


class TestAuthRoutes:
    """認證路由測試"""
    
    def test_login_success(self, client):
        """測試登入成功"""
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user' in data
    
    def test_login_invalid_credentials(self, client):
        """測試登入失敗 - 無效憑證"""
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """測試登入失敗 - 缺少欄位"""
        response = client.post('/api/login', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400
    
    def test_register_success(self, client):
        """測試註冊成功"""
        response = client.post('/api/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 201
    
    def test_register_duplicate_email(self, client):
        """測試註冊失敗 - 重複郵箱"""
        response = client.post('/api/register', json={
            'username': 'duplicate',
            'email': 'test@example.com',  # 已存在的郵箱
            'password': 'password123'
        })
        
        assert response.status_code == 400


class TestUserRoutes:
    """用戶路由測試"""
    
    def test_get_profile_success(self, client):
        """測試獲取用戶資料成功"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            token = generate_token(user.id)
        
        response = client.get('/api/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'testuser'
    
    def test_update_profile_success(self, client):
        """測試更新用戶資料成功"""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            token = generate_token(user.id)
        
        response = client.put('/api/profile', 
            headers={'Authorization': f'Bearer {token}'},
            json={'username': 'updateduser'}
        )
        
        assert response.status_code == 200


class TestAdminRoutes:
    """管理員路由測試"""
    
    def test_get_users_success(self, client):
        """測試獲取用戶列表成功"""
        with app.app_context():
            admin = User.query.filter_by(role='admin').first()
            token = generate_token(admin.id, role='admin')
        
        response = client.get('/api/admin/users', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
    
    def test_get_users_non_admin(self, client):
        """測試非管理員訪問用戶列表"""
        with app.app_context():
            user = User.query.filter_by(role='user').first()
            token = generate_token(user.id, role='user')
        
        response = client.get('/api/admin/users', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 403


class TestHealthEndpoint:
    """健康檢查端點測試"""
    
    def test_health_check(self, client):
        """測試健康檢查端點"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data
        assert 'version' in data


class TestErrorHandling:
    """錯誤處理測試"""
    
    def test_404_error(self, client):
        """測試 404 錯誤"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """測試無效 JSON"""
        response = client.post('/api/login', 
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_missing_content_type(self, client):
        """測試缺少 Content-Type"""
        response = client.post('/api/login', data='{}')
        assert response.status_code == 400
