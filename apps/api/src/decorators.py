from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from src.models.user import User

def require_role(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if user and user.role == role:
                return fn(*args, **kwargs)
            else:
                return jsonify({"msg": "Permission denied"}), 403
        return wrapper
    return decorator

