from flask import Blueprint, jsonify, request
from models.user import User, db
from decorators import require_role

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@require_role('admin')
def get_all_users():
    """
    獲取所有用戶列表（僅管理員）
    
    Headers:
        Authorization: Bearer <admin_token>
    
    Returns:
        JSON: 用戶列表
    """
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users', 'details': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_role('admin')
def get_user_by_id(user_id):
    """
    根據 ID 獲取用戶信息（僅管理員）
    
    Args:
        user_id (int): 用戶 ID
    
    Headers:
        Authorization: Bearer <admin_token>
    
    Returns:
        JSON: 用戶信息
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user', 'details': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@require_role('admin')
def update_user_role(user_id):
    """
    更新用戶角色（僅管理員）
    
    Args:
        user_id (int): 用戶 ID
    
    Request Body:
        {
            "role": "admin" | "user"
        }
    
    Headers:
        Authorization: Bearer <admin_token>
    
    Returns:
        JSON: 更新後的用戶信息
    """
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['admin', 'user']:
            return jsonify({'error': 'Invalid role. Must be "admin" or "user"'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.role = new_role
        db.session.commit()
        
        return jsonify({
            'message': 'User role updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user role', 'details': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@require_role('admin')
def update_user_status(user_id):
    """
    更新用戶狀態（僅管理員）
    
    Args:
        user_id (int): 用戶 ID
    
    Request Body:
        {
            "is_active": true | false
        }
    
    Headers:
        Authorization: Bearer <admin_token>
    
    Returns:
        JSON: 更新後的用戶信息
    """
    try:
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({'error': 'is_active field is required'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = bool(is_active)
        db.session.commit()
        
        return jsonify({
            'message': 'User status updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user status', 'details': str(e)}), 500

