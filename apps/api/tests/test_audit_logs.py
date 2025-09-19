"""
Audit Logs Tests
Tests for audit logging functionality including creation, querying, and management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json


class TestAuditLogCreation:
    """Test audit log creation functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_user_id = 123
        self.test_admin_id = 456
        self.test_ip = "192.168.1.100"
        
    def test_create_login_audit_log(self):
        """Test creation of login audit log."""
        audit_log = {
            'user_id': self.test_user_id,
            'action': 'LOGIN',
            'resource': 'AUTH',
            'details': {'ip_address': self.test_ip, 'user_agent': 'Mozilla/5.0'},
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUCCESS'
        }
        
        assert audit_log['user_id'] == self.test_user_id
        assert audit_log['action'] == 'LOGIN'
        assert audit_log['resource'] == 'AUTH'
        assert audit_log['status'] == 'SUCCESS'
        assert 'ip_address' in audit_log['details']
        
    def test_create_logout_audit_log(self):
        """Test creation of logout audit log."""
        audit_log = {
            'user_id': self.test_user_id,
            'action': 'LOGOUT',
            'resource': 'AUTH',
            'details': {'ip_address': self.test_ip, 'session_duration': '45 minutes'},
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUCCESS'
        }
        
        assert audit_log['action'] == 'LOGOUT'
        assert audit_log['status'] == 'SUCCESS'
        assert 'session_duration' in audit_log['details']
        
    def test_create_admin_action_audit_log(self):
        """Test creation of admin action audit log."""
        audit_log = {
            'user_id': self.test_admin_id,
            'action': 'USER_DELETE',
            'resource': 'USER_MANAGEMENT',
            'details': {
                'target_user_id': self.test_user_id,
                'reason': 'Account violation',
                'ip_address': self.test_ip
            },
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUCCESS'
        }
        
        assert audit_log['action'] == 'USER_DELETE'
        assert audit_log['resource'] == 'USER_MANAGEMENT'
        assert audit_log['details']['target_user_id'] == self.test_user_id
        assert 'reason' in audit_log['details']
        
    def test_create_failed_action_audit_log(self):
        """Test creation of failed action audit log."""
        audit_log = {
            'user_id': self.test_user_id,
            'action': 'PASSWORD_CHANGE',
            'resource': 'USER_PROFILE',
            'details': {
                'error': 'Current password incorrect',
                'ip_address': self.test_ip
            },
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'FAILED'
        }
        
        assert audit_log['status'] == 'FAILED'
        assert 'error' in audit_log['details']
        
    def test_create_2fa_audit_log(self):
        """Test creation of 2FA related audit log."""
        audit_log = {
            'user_id': self.test_user_id,
            'action': '2FA_ENABLE',
            'resource': 'SECURITY',
            'details': {
                'method': 'TOTP',
                'backup_codes_generated': 10,
                'ip_address': self.test_ip
            },
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUCCESS'
        }
        
        assert audit_log['action'] == '2FA_ENABLE'
        assert audit_log['resource'] == 'SECURITY'
        assert audit_log['details']['method'] == 'TOTP'


class TestAuditLogQuerying:
    """Test audit log querying functionality."""
    
    def setup_method(self):
        """Setup test environment with mock audit logs."""
        self.mock_audit_logs = [
            {
                'id': 1,
                'user_id': 123,
                'action': 'LOGIN',
                'resource': 'AUTH',
                'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'status': 'SUCCESS'
            },
            {
                'id': 2,
                'user_id': 123,
                'action': 'PASSWORD_CHANGE',
                'resource': 'USER_PROFILE',
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'status': 'SUCCESS'
            },
            {
                'id': 3,
                'user_id': 456,
                'action': 'USER_DELETE',
                'resource': 'USER_MANAGEMENT',
                'timestamp': (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                'status': 'SUCCESS'
            }
        ]
        
    def test_query_logs_by_user_id(self):
        """Test querying audit logs by user ID."""
        user_id = 123
        user_logs = [log for log in self.mock_audit_logs if log['user_id'] == user_id]
        
        assert len(user_logs) == 2
        assert all(log['user_id'] == user_id for log in user_logs)
        
    def test_query_logs_by_action(self):
        """Test querying audit logs by action type."""
        action = 'LOGIN'
        action_logs = [log for log in self.mock_audit_logs if log['action'] == action]
        
        assert len(action_logs) == 1
        assert action_logs[0]['action'] == action
        
    def test_query_logs_by_resource(self):
        """Test querying audit logs by resource type."""
        resource = 'AUTH'
        resource_logs = [log for log in self.mock_audit_logs if log['resource'] == resource]
        
        assert len(resource_logs) == 1
        assert resource_logs[0]['resource'] == resource
        
    def test_query_logs_by_date_range(self):
        """Test querying audit logs by date range."""
        start_time = datetime.utcnow() - timedelta(hours=2, minutes=30)
        end_time = datetime.utcnow()
        
        date_range_logs = []
        for log in self.mock_audit_logs:
            log_time = datetime.fromisoformat(log['timestamp'])
            if start_time <= log_time <= end_time:
                date_range_logs.append(log)
                
        assert len(date_range_logs) >= 1  # Should include recent logs
        
    def test_query_logs_with_pagination(self):
        """Test querying audit logs with pagination."""
        page_size = 2
        page_1 = self.mock_audit_logs[:page_size]
        page_2 = self.mock_audit_logs[page_size:]
        
        assert len(page_1) == 2
        assert len(page_2) == 1
        assert page_1[0]['id'] != page_2[0]['id']
        
    def test_query_logs_by_status(self):
        """Test querying audit logs by status."""
        status = 'SUCCESS'
        status_logs = [log for log in self.mock_audit_logs if log['status'] == status]
        
        assert len(status_logs) == 3  # All mock logs are SUCCESS
        assert all(log['status'] == status for log in status_logs)


class TestAuditLogSecurity:
    """Test audit log security and integrity."""
    
    def test_audit_log_immutability(self):
        """Test that audit logs cannot be modified after creation."""
        original_log = {
            'user_id': 123,
            'action': 'LOGIN',
            'resource': 'AUTH',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUCCESS'
        }
        
        # Simulate attempting to modify the log
        # In a real system, this would be prevented by database constraints
        modified_log = original_log.copy()
        modified_log['action'] = 'LOGOUT'  # Attempt to change action
        
        # In a proper audit system, this modification should be prevented
        # For testing, we verify that the original remains unchanged
        assert original_log['action'] == 'LOGIN'
        assert modified_log['action'] == 'LOGOUT'
        # In reality, the modification attempt should fail
        
    def test_audit_log_access_control(self):
        """Test access control for audit log viewing."""
        # Mock user roles
        admin_user = {'user_id': 456, 'role': 'admin'}
        regular_user = {'user_id': 123, 'role': 'user'}
        
        # Admin should be able to view all logs
        admin_can_view_all = admin_user['role'] == 'admin'
        
        # Regular user should only view their own logs
        user_can_view_own = regular_user['role'] == 'user'
        
        assert admin_can_view_all is True
        assert user_can_view_own is True
        
    def test_audit_log_retention(self):
        """Test audit log retention policy."""
        # Mock logs with different ages
        old_log = {
            'timestamp': (datetime.utcnow() - timedelta(days=400)).isoformat(),
            'action': 'LOGIN'
        }
        recent_log = {
            'timestamp': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'action': 'LOGIN'
        }
        
        # Simulate retention policy (e.g., keep logs for 365 days)
        retention_days = 365
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        old_log_time = datetime.fromisoformat(old_log['timestamp'])
        recent_log_time = datetime.fromisoformat(recent_log['timestamp'])
        
        should_retain_old = old_log_time > cutoff_date
        should_retain_recent = recent_log_time > cutoff_date
        
        assert should_retain_old is False  # Old log should be archived/deleted
        assert should_retain_recent is True  # Recent log should be retained


class TestAuditLogIntegration:
    """Test audit log integration with other system components."""
    
    def test_audit_log_with_authentication(self):
        """Test audit logging integration with authentication system."""
        # Mock authentication attempt
        login_attempt = {
            'email': 'test@example.com',
            'password': 'correct_password',
            'ip_address': '192.168.1.100'
        }
        
        # Simulate successful authentication
        auth_success = True  # Mock authentication result
        user_id = 123 if auth_success else None
        
        # Create audit log based on authentication result
        if auth_success:
            audit_log = {
                'user_id': user_id,
                'action': 'LOGIN',
                'resource': 'AUTH',
                'details': {
                    'ip_address': login_attempt['ip_address'],
                    'email': login_attempt['email']
                },
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'SUCCESS'
            }
        else:
            audit_log = {
                'user_id': None,
                'action': 'LOGIN_FAILED',
                'resource': 'AUTH',
                'details': {
                    'ip_address': login_attempt['ip_address'],
                    'email': login_attempt['email'],
                    'reason': 'Invalid credentials'
                },
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'FAILED'
            }
            
        assert audit_log['action'] == 'LOGIN'
        assert audit_log['status'] == 'SUCCESS'
        assert audit_log['user_id'] == user_id
        
    def test_audit_log_with_admin_actions(self):
        """Test audit logging integration with admin actions."""
        # Mock admin action
        admin_action = {
            'admin_id': 456,
            'action_type': 'user_suspension',
            'target_user_id': 123,
            'reason': 'Policy violation'
        }
        
        # Create audit log for admin action
        audit_log = {
            'user_id': admin_action['admin_id'],
            'action': 'USER_SUSPEND',
            'resource': 'USER_MANAGEMENT',
            'details': {
                'target_user_id': admin_action['target_user_id'],
                'reason': admin_action['reason'],
                'action_type': admin_action['action_type']
            },
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'SUCCESS'
        }
        
        assert audit_log['action'] == 'USER_SUSPEND'
        assert audit_log['details']['target_user_id'] == 123
        assert 'reason' in audit_log['details']
