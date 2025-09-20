"""
Coverage Boost Tests - 提升測試覆蓋率的簡單測試
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.main import app
from src.database import db
from src.models.user import User
from src.models.audit_log import AuditLog, AuditActions
from src.models.jwt_blacklist import JWTBlacklist
from src.services.email_service import get_email_service, EmailService, MockEmailService
from src.services.two_factor_service import get_two_factor_service, TwoFactorService, MockTwoFactorService


@pytest.fixture
def client():
    """測試客戶端"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # 創建測試用戶
            test_user = User(
                username='testuser',
                email='test@example.com',
                role='user',
                is_active=True,
                is_email_verified=True
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                
        yield client


class TestModelMethods:
    """測試模型方法"""
    
    def test_user_model_methods(self, client):
        """測試用戶模型方法"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # 測試 to_dict 方法
            user_dict = user.to_dict()
            assert 'id' in user_dict
            assert 'email' in user_dict
            assert 'username' in user_dict
            
            # 測試 is_admin 方法
            assert not user.is_admin()
            
            user.role = 'admin'
            assert user.is_admin()
            
            # 測試密碼驗證
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_audit_log_model(self, client):
        """測試審計日誌模型"""
        with app.app_context():
            # 測試創建審計日誌
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
            
            # 測試 to_dict 方法
            log_dict = log_entry.to_dict()
            assert 'id' in log_dict
            assert 'action' in log_dict
            assert 'user_id' in log_dict
    
    def test_jwt_blacklist_model(self, client):
        """測試 JWT 黑名單模型"""
        with app.app_context():
            from datetime import datetime, timedelta
            
            expires = datetime.utcnow() + timedelta(hours=1)
            # 測試添加權杖到黑名單
            JWTBlacklist.add_to_blacklist(jti='test_jti_123', user_id=1, expires_at=expires)
            
            # 測試檢查權杖是否在黑名單中
            assert JWTBlacklist.is_blacklisted('test_jti_123')
            assert not JWTBlacklist.is_blacklisted('non_existent_jti')
            
            # 測試 to_dict 方法
            blacklist_entry = JWTBlacklist.query.filter_by(jti='test_jti_123').first()
            assert blacklist_entry is not None
            blacklist_dict = blacklist_entry.to_dict()
            assert 'id' in blacklist_dict
            assert 'jti' in blacklist_dict
            assert blacklist_dict['jti'] == 'test_jti_123'


class TestServices:
    """測試服務類別"""
    
    def test_email_service(self):
        """測試電子郵件服務"""
        # 測試獲取服務實例
        service = get_email_service()
        assert service is not None
        
        # 測試實際服務
        real_service = EmailService()
        result = real_service.send_verification_email('test@example.com', 'http://example.com/verify')
        assert isinstance(result, bool)
        
        # 測試 Mock 服務
        mock_service = MockEmailService()
        result = mock_service.send_verification_email('test@example.com', 'http://example.com/verify')
        assert result is True
        assert len(mock_service.sent_emails) == 1
        
        # 測試清除郵件記錄
        mock_service.clear_sent_emails()
        assert len(mock_service.sent_emails) == 0
    
    def test_two_factor_service(self):
        """測試 2FA 服務"""
        # 測試獲取服務實例
        service = get_two_factor_service()
        assert service is not None
        
        # 測試實際服務
        real_service = TwoFactorService()
        secret = real_service.generate_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0
        
        # 測試生成備份碼
        backup_codes = real_service.generate_backup_codes()
        assert isinstance(backup_codes, list)
        assert len(backup_codes) == 10
        
        # 測試雜湊備份碼
        code = backup_codes[0]
        hashed = real_service.hash_backup_code(code)
        assert isinstance(hashed, str)
        assert real_service.verify_backup_code(code, hashed)
        
        # 測試 Mock 服務
        mock_service = MockTwoFactorService()
        mock_secret = mock_service.generate_secret()
        assert mock_secret == "JBSWY3DPEHPK3PXP"
        
        # 測試 OTP 驗證
        assert mock_service.verify_otp(mock_secret, "123456")
        assert not mock_service.verify_otp(mock_secret, "000000")


class TestUtilityFunctions:
    """測試工具函數"""
    
    def test_app_routes(self, client):
        """測試應用程式路由"""
        # 測試根路由
        response = client.get('/')
        assert response.status_code == 200
        
        # 測試健康檢查
        response = client.get('/test-deployment')
        assert response.status_code == 200
        
        # 測試文檔路由
        response = client.get('/docs')
        assert response.status_code == 200
    
    def test_database_operations(self, client):
        """測試資料庫操作"""
        with app.app_context():
            # 測試用戶查詢
            users = User.query.all()
            assert len(users) >= 1
            
            # 測試用戶過濾
            user = User.query.filter_by(email='test@example.com').first()
            assert user is not None
            assert user.email == 'test@example.com'
    
    def test_configuration(self, client):
        """測試應用程式配置"""
        with app.app_context():
            # 測試配置值
            assert app.config['TESTING'] is True
            assert 'JWT_SECRET_KEY' in app.config
            assert 'SQLALCHEMY_DATABASE_URI' in app.config


class TestErrorHandling:
    """測試錯誤處理"""
    
    def test_404_routes(self, client):
        """測試 404 路由"""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """測試不允許的方法"""
        response = client.post('/')
        assert response.status_code == 405
    
    def test_invalid_json(self, client):
        """測試無效的 JSON"""
        response = client.post('/api/register', 
                             data='invalid json',
                             content_type='application/json')
        print(f"Invalid JSON test response: {response.data.decode()}")
        assert response.status_code == 400


class TestDatabaseModels:
    """測試資料庫模型的額外方法"""
    
    def test_user_model_edge_cases(self, client):
        """測試用戶模型的邊界情況"""
        with app.app_context():
            # 測試創建新用戶
            new_user = User(
                username='newuser',
                email='new@example.com',
                role='user'
            )
            new_user.set_password('newpassword')
            
            db.session.add(new_user)
            db.session.commit()
            
            # 測試查詢新用戶
            found_user = User.query.filter_by(username='newuser').first()
            assert found_user is not None
            assert found_user.check_password('newpassword')
    
    def test_audit_log_filtering(self, client):
        """測試審計日誌過濾"""
        with app.app_context():
            # 清空審計日誌
            db.session.query(AuditLog).delete()
            db.session.commit()
            
            # 創建多個審計日誌條目
            AuditLog.log_action(AuditActions.LOGIN, 1, {}, '127.0.0.1', 'success')
            AuditLog.log_action(AuditActions.LOGOUT, 1, {}, '127.0.0.1', 'success')
            
            # 測試按動作過濾
            login_logs = AuditLog.query.filter_by(action=AuditActions.LOGIN).all()
            assert len(login_logs) == 1
            
            logout_logs = AuditLog.query.filter_by(action=AuditActions.LOGOUT).all()
            assert len(logout_logs) == 1
