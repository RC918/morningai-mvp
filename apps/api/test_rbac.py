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