"""
Decorators 模組測試
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

from src.main import app
from src.database import db
from src.models.user import User
from src.decorators import token_required


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
                
        yield client


@pytest.fixture
def auth_headers(client):
    """獲取認證標頭"""
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    token = data.get('access_token')
    
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers(client):
    """獲取管理員認證標頭"""
    response = client.post('/api/login', json={
        'email': 'admin@example.com',
        'password': 'password123'
    })
    
    data = json.loads(response.data)
    token = data.get('access_token')
    
    return {'Authorization': f'Bearer {token}'}


class TestTokenRequired:
    """token_required 裝飾器測試"""
    
    def test_missing_authorization_header(self, client):
        """測試缺少 Authorization 標頭"""
        response = client.get('/api/profile')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'token is missing' in data['error']
    
    def test_invalid_authorization_format(self, client):
        """測試無效的 Authorization 格式"""
        response = client.get('/api/profile', headers={
            'Authorization': 'InvalidFormat'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'token is missing' in data['error']
    
    def test_invalid_token(self, client):
        """測試無效的權杖"""
        response = client.get('/api/profile', headers={
            'Authorization': 'Bearer invalid_token'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'token is invalid' in data['error']
    
    def test_valid_token(self, client, auth_headers):
        """測試有效的權杖"""
        response = client.get('/api/profile', headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_inactive_user(self, client):
        """測試非活躍用戶"""
        # 先登入獲取權杖
        response = client.post('/api/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        data = json.loads(response.data)
        token = data.get('access_token')
        
        # 將用戶設為非活躍
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            user.is_active = False
            db.session.commit()
        
        # 使用權杖訪問受保護的端點
        response = client.get('/api/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'user is inactive' in data['error']


class TestAdminAccess:
    """管理員權限測試"""
    
    def test_non_admin_access(self, client, auth_headers):
        """測試非管理員訪問管理員端點"""
        response = client.get('/api/admin/users', headers=auth_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'forbidden' in data['error']
    
    def test_admin_access(self, client, admin_headers):
        """測試管理員訪問管理員端點"""
        response = client.get('/api/admin/users', headers=admin_headers)
        
        assert response.status_code == 200


class TestDecoratorChaining:
    """裝飾器鏈測試"""
    
    def test_token_and_admin_required(self, client, admin_headers):
        """測試同時需要權杖和管理員權限的端點"""
        response = client.get('/api/admin/blacklist', headers=admin_headers)
        
        assert response.status_code == 200
    
    def test_token_and_admin_required_with_user_token(self, client, auth_headers):
        """測試使用普通用戶權杖訪問管理員端點"""
        response = client.get('/api/admin/blacklist', headers=auth_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'forbidden' in data['error']


class TestTokenBlacklist:
    """權杖黑名單測試"""
    
    def test_blacklisted_token(self, client, auth_headers):
        """測試被列入黑名單的權杖"""
        # 先登出，將權杖加入黑名單
        logout_response = client.post('/api/auth/logout', headers=auth_headers)
        assert logout_response.status_code == 200
        
        # 嘗試使用已登出的權杖
        response = client.get('/api/profile', headers=auth_headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'token is blacklisted' in data['error']
    
    def test_tokens_valid_since_check(self, client, auth_headers):
        """測試 tokens_valid_since 檢查"""
        # 先執行「登出所有裝置」
        logout_all_response = client.post('/api/auth/logout-all', headers=auth_headers)
        assert logout_all_response.status_code == 200
        
        # 嘗試使用舊權杖
        response = client.get('/api/profile', headers=auth_headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'token is invalid' in data['error']
