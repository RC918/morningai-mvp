import pytest
from src.main import app
from src.models.user import User
from src.utils.db import db
from unittest.mock import patch

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def get_jwt_token(client, email, password):
    response = client.post(
        '/auth/login',
        json={'email': email, 'password': password}
    )
    return response.json['access_token']

def test_rbac_admin_access(client):
    # Create an admin user
    admin_user = User(email='admin@example.com', password='adminpassword', role='admin')
    db.session.add(admin_user)
    db.session.commit()

    # Get admin token
    admin_token = get_jwt_token(client, 'admin@example.com', 'adminpassword')

    # Test admin access to /admin/users
    response = client.get(
        '/admin/users',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 200

def test_rbac_user_access(client):
    # Create a regular user
    regular_user = User(email='user@example.com', password='userpassword', role='user')
    db.session.add(regular_user)
    db.session.commit()

    # Get regular user token
    user_token = get_jwt_token(client, 'user@example.com', 'userpassword')

    # Test regular user access to /admin/users (should be 403 Forbidden)
    response = client.get(
        '/admin/users',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    assert response.status_code == 403

def test_rbac_unauthenticated_access(client):
    # Test unauthenticated access to /admin/users (should be 401 Unauthorized)
    response = client.get('/admin/users')
    assert response.status_code == 401


