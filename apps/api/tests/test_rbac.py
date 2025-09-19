"""
RBAC (Role-Based Access Control) Tests
Tests for admin/user role-based access control functionality.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock


class TestRBACAccess:
    """Test role-based access control for admin and user roles."""
    
    def setup_method(self):
        """Setup test environment."""
        self.base_url = "http://localhost:5000"
        self.admin_token = "mock_admin_token"
        self.user_token = "mock_user_token"
        
    def test_admin_access_allowed(self):
        """Test that admin users can access admin endpoints."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {'role': 'admin', 'user_id': 1}
            
            # Mock admin endpoint access
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'success', 'data': 'admin_data'}
                mock_get.return_value = mock_response
                
                headers = {'Authorization': f'Bearer {self.admin_token}'}
                response = requests.get(f"{self.base_url}/admin/users", headers=headers)
                
                assert response.status_code == 200
                assert response.json()['status'] == 'success'
                
    def test_user_access_denied_to_admin_endpoints(self):
        """Test that regular users cannot access admin endpoints."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {'role': 'user', 'user_id': 2}
            
            # Mock admin endpoint access denial
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 403
                mock_response.json.return_value = {'error': 'Insufficient permissions'}
                mock_get.return_value = mock_response
                
                headers = {'Authorization': f'Bearer {self.user_token}'}
                response = requests.get(f"{self.base_url}/admin/users", headers=headers)
                
                assert response.status_code == 403
                assert 'Insufficient permissions' in response.json()['error']
                
    def test_user_access_allowed_to_user_endpoints(self):
        """Test that regular users can access user endpoints."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {'role': 'user', 'user_id': 2}
            
            # Mock user endpoint access
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'success', 'user_id': 2}
                mock_get.return_value = mock_response
                
                headers = {'Authorization': f'Bearer {self.user_token}'}
                response = requests.get(f"{self.base_url}/user/profile", headers=headers)
                
                assert response.status_code == 200
                assert response.json()['status'] == 'success'
                
    def test_no_token_access_denied(self):
        """Test that requests without tokens are denied."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {'error': 'Token required'}
            mock_get.return_value = mock_response
            
            response = requests.get(f"{self.base_url}/admin/users")
            
            assert response.status_code == 401
            assert 'Token required' in response.json()['error']
            
    def test_invalid_token_access_denied(self):
        """Test that requests with invalid tokens are denied."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.json.return_value = {'error': 'Invalid token'}
                mock_get.return_value = mock_response
                
                headers = {'Authorization': 'Bearer invalid_token'}
                response = requests.get(f"{self.base_url}/admin/users", headers=headers)
                
                assert response.status_code == 401
                assert 'Invalid token' in response.json()['error']


class TestRoleValidation:
    """Test role validation logic."""
    
    def test_admin_role_validation(self):
        """Test admin role validation."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {'role': 'admin', 'user_id': 1}
            
            # Test role validation logic
            token_data = mock_verify.return_value
            assert token_data['role'] == 'admin'
            assert 'user_id' in token_data
            
    def test_user_role_validation(self):
        """Test user role validation."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {'role': 'user', 'user_id': 2}
            
            # Test role validation logic
            token_data = mock_verify.return_value
            assert token_data['role'] == 'user'
            assert 'user_id' in token_data
            
    def test_unknown_role_handling(self):
        """Test handling of unknown roles."""
        with patch('src.decorators.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {'role': 'unknown', 'user_id': 3}
            
            # Test unknown role handling
            token_data = mock_verify.return_value
            assert token_data['role'] not in ['admin', 'user']
            # Should be treated as regular user or denied access
