import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from datetime import timedelta
from models import User, db

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_tokens(user_id, tenant_id=None):
    """Create access and refresh tokens for a user"""
    additional_claims = {}
    if tenant_id:
        additional_claims["tenant_id"] = tenant_id
    
    access_token = create_access_token(
        identity=str(user_id),  # Convert to string
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity=str(user_id),  # Convert to string
        additional_claims=additional_claims,
        expires_delta=timedelta(days=30)
    )
    
    return access_token, refresh_token

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    user = User.query.filter_by(username=username).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None

def register_user(username, email, password, tenant_id):
    """Register a new user"""
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return None, "Username already exists"
    
    if User.query.filter_by(email=email).first():
        return None, "Email already exists"
    
    # Create new user
    hashed_password = hash_password(password)
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        tenant_id=tenant_id
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"
