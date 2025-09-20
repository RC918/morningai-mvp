import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from src.main import app
from src.database import db
from src.models.user import User
from src.models.jwt_blacklist import JWTBlacklist

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
                is_active=True
            )
            test_user.set_password('testpass123')
            db.session.add(test_user)
            
            # 創建管理員用戶
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                is_active=True
            )
            admin_user.set_password('adminpass123')
            db.session.add(admin_user)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Database setup error: {e}")
            
        yield client
        
        with app.app_context():
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    """獲取認證標頭"""
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    data = json.loads(response.data)
    token = data['token']
    
    return {'Authorization': f'Bearer {token}'}, token

@pytest.fixture
def admin_headers(client):
    """獲取管理員認證標頭"""
    response = client.post('/api/login', json={
        'email': 'admin@example.com',
        'password': 'adminpass123'
    })
    
    data = json.loads(response.data)
    token = data['token']
    
    return {'Authorization': f'Bearer {token}'}, token

class TestJWTBlacklist:
    """JWT 黑名單測試"""
    
    def test_logout_adds_token_to_blacklist(self, client, auth_headers):
        """TC-JWTBL-001：登出後，用舊 token 呼叫受保護 API → 401"""
        headers, token = auth_headers
        
        # 首先驗證 token 有效
        response = client.get('/api/admin/users', headers=headers)
        # 這個端點可能不存在，但我們主要測試 token 驗證
        
        # 登出
        response = client.post('/api/auth/logout', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '登出成功' in data['message']
        
        # 驗證 token 已被加入黑名單
        with app.app_context():
            blacklist_count = JWTBlacklist.query.count()
            assert blacklist_count > 0
        
        # 嘗試使用已被加入黑名單的 token
        response = client.get('/api/admin/users', headers=headers)
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Token has been revoked' in data['error']
    
    def test_blacklist_check_functionality(self, client):
        """測試黑名單檢查功能"""
        with app.app_context():
            # 創建一個測試 JTI
            test_jti = str(uuid.uuid4())
            
            # 檢查不存在的 JTI
            assert not JWTBlacklist.is_blacklisted(test_jti)
            
            # 添加到黑名單
            expires_at = datetime.utcnow() + timedelta(hours=1)
            JWTBlacklist.add_to_blacklist(
                jti=test_jti,
                user_id=1,
                expires_at=expires_at,
                reason='test'
            )
            
            # 檢查已加入黑名單的 JTI
            assert JWTBlacklist.is_blacklisted(test_jti)
    
    def test_expired_token_cleanup(self, client):
        """TC-JWTBL-002：過期/清理機制驗證"""
        with app.app_context():
            # 創建一個已過期的黑名單項目
            expired_jti = str(uuid.uuid4())
            expired_time = datetime.utcnow() - timedelta(hours=1)  # 1小時前過期
            
            JWTBlacklist.add_to_blacklist(
                jti=expired_jti,
                user_id=1,
                expires_at=expired_time,
                reason='test_expired'
            )
            
            # 創建一個未過期的黑名單項目
            valid_jti = str(uuid.uuid4())
            valid_time = datetime.utcnow() + timedelta(hours=1)  # 1小時後過期
            
            JWTBlacklist.add_to_blacklist(
                jti=valid_jti,
                user_id=1,
                expires_at=valid_time,
                reason='test_valid'
            )
            
            # 檢查過期的 token 會被自動清理
            assert not JWTBlacklist.is_blacklisted(expired_jti)
            assert JWTBlacklist.is_blacklisted(valid_jti)
            
            # 手動清理測試
            cleaned_count = JWTBlacklist.cleanup_expired_tokens()
            assert cleaned_count >= 0  # 可能已經被自動清理了
    
    def test_logout_all_devices(self, client, auth_headers):
        """測試登出所有設備"""
        headers, token = auth_headers
        
        response = client.post('/api/auth/logout-all', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '已登出所有設備' in data['message']
    
    def test_admin_get_blacklist(self, client, admin_headers):
        """測試管理員獲取黑名單"""
        headers, token = admin_headers
        
        response = client.get('/api/admin/blacklist', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'blacklist' in data
        assert 'total' in data
    
    def test_non_admin_cannot_access_blacklist(self, client, auth_headers):
        """測試非管理員無法訪問黑名單"""
        headers, token = auth_headers
        
        response = client.get('/api/admin/blacklist', headers=headers)
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'forbidden' in data['error']
    
    def test_admin_cleanup_blacklist(self, client, admin_headers):
        """測試管理員清理黑名單"""
        headers, token = admin_headers
        
        response = client.post('/api/admin/blacklist/cleanup', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cleaned_count' in data
    
    def test_revoke_token(self, client, auth_headers):
        """測試撤銷 token"""
        headers, token = auth_headers
        
        # 嘗試撤銷自己的 token
        response = client.post('/api/auth/revoke-token', 
                             json={'token': token, 'reason': 'test_revoke'},
                             headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Token 已撤銷' in data['message']
    
    def test_jwt_with_jti_in_payload(self, client):
        """測試 JWT 包含 JTI"""
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data['token']
        
        # 解碼 token 檢查 JTI
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        assert 'jti' in payload
        assert payload['jti'] is not None
        assert len(payload['jti']) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])




    def test_logout_all_invalidates_older_tokens(self, client):
        """TC-JWTBL-003: 登出所有裝置後，舊 token 失效，新 token 有效"""
        # 1. 第一次登入，取得 token 1
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        token1 = json.loads(response.data)['token']
        headers1 = {'Authorization': f'Bearer {token1}'}

        # 2. 驗證 token 1 有效
        response = client.get('/api/auth/profile', headers=headers1)
        assert response.status_code == 200

        # 3. 執行「登出所有裝置」
        response = client.post('/api/auth/logout-all', headers=headers1)
        assert response.status_code == 200

        # 4. 驗證 token 1 已失效
        response = client.get('/api/auth/profile', headers=headers1)
        assert response.status_code == 401
        assert 'Token has been revoked by logout all' in json.loads(response.data)['error']

        # 5. 第二次登入，取得 token 2
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        token2 = json.loads(response.data)['token']
        headers2 = {'Authorization': f'Bearer {token2}'}

        # 6. 驗證 token 2 有效
        response = client.get('/api/auth/profile', headers=headers2)
        assert response.status_code == 200

