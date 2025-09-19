from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import secrets
import json

from src.database import db
from src.models.user import User
from src.models.tenant import Tenant, TenantInvitation
from src.audit_log import audit_log

tenant_bp = Blueprint('tenant', __name__)

@tenant_bp.route('/tenants', methods=['GET'])
@jwt_required()
@audit_log(action="list_tenants", resource_type="tenant")
def list_tenants():
    """列出所有租戶 (僅限系統管理員)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin():
        return jsonify({"message": "權限不足"}), 403
    
    tenants = Tenant.query.all()
    return jsonify({
        "tenants": [tenant.to_dict() for tenant in tenants]
    }), 200

@tenant_bp.route('/tenants', methods=['POST'])
@jwt_required()
@audit_log(action="create_tenant", resource_type="tenant")
def create_tenant():
    """建立新租戶"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    data = request.get_json()
    
    # 驗證必填欄位
    if not data.get('name') or not data.get('slug'):
        return jsonify({"message": "租戶名稱和 slug 為必填欄位"}), 400
    
    # 檢查 slug 是否已存在
    if Tenant.query.filter_by(slug=data['slug']).first():
        return jsonify({"message": "此 slug 已被使用"}), 400
    
    # 檢查自訂網域是否已存在
    if data.get('domain') and Tenant.query.filter_by(domain=data['domain']).first():
        return jsonify({"message": "此網域已被使用"}), 400
    
    try:
        # 建立租戶
        tenant = Tenant(
            name=data['name'],
            slug=data['slug'],
            domain=data.get('domain'),
            description=data.get('description'),
            plan=data.get('plan', 'free'),
            max_users=data.get('max_users', 5),
            max_storage_gb=data.get('max_storage_gb', 1)
        )
        
        # 設定試用期 (30 天)
        if tenant.is_trial:
            tenant.trial_ends_at = datetime.utcnow() + timedelta(days=30)
        
        db.session.add(tenant)
        db.session.flush()  # 取得 tenant.id
        
        # 將建立者設為租戶擁有者
        user.tenant_id = tenant.id
        user.tenant_role = 'owner'
        
        db.session.commit()
        
        return jsonify({
            "message": "租戶建立成功",
            "tenant": tenant.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"建立租戶失敗: {str(e)}"}), 500

@tenant_bp.route('/tenants/<int:tenant_id>', methods=['GET'])
@jwt_required()
@audit_log(action="get_tenant", resource_type="tenant")
def get_tenant(tenant_id):
    """取得租戶詳細資訊"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return jsonify({"message": "租戶不存在"}), 404
    
    # 檢查權限：系統管理員或租戶成員
    if not (user.is_admin() or user.tenant_id == tenant_id):
        return jsonify({"message": "權限不足"}), 403
    
    tenant_data = tenant.to_dict()
    tenant_data['usage_stats'] = tenant.get_usage_stats()
    
    return jsonify({"tenant": tenant_data}), 200

@tenant_bp.route('/tenants/<int:tenant_id>', methods=['PUT'])
@jwt_required()
@audit_log(action="update_tenant", resource_type="tenant")
def update_tenant(tenant_id):
    """更新租戶資訊"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return jsonify({"message": "租戶不存在"}), 404
    
    # 檢查權限：系統管理員或租戶擁有者/管理員
    if not (user.is_admin() or (user.tenant_id == tenant_id and user.tenant_role in ['owner', 'admin'])):
        return jsonify({"message": "權限不足"}), 403
    
    data = request.get_json()
    
    try:
        # 更新允許的欄位
        if 'name' in data:
            tenant.name = data['name']
        if 'description' in data:
            tenant.description = data['description']
        if 'domain' in data and data['domain'] != tenant.domain:
            # 檢查新網域是否已被使用
            if data['domain'] and Tenant.query.filter_by(domain=data['domain']).first():
                return jsonify({"message": "此網域已被使用"}), 400
            tenant.domain = data['domain']
        
        # 只有系統管理員可以更新這些欄位
        if user.is_admin():
            if 'plan' in data:
                tenant.plan = data['plan']
            if 'max_users' in data:
                tenant.max_users = data['max_users']
            if 'max_storage_gb' in data:
                tenant.max_storage_gb = data['max_storage_gb']
            if 'is_active' in data:
                tenant.is_active = data['is_active']
        
        tenant.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "租戶更新成功",
            "tenant": tenant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"更新租戶失敗: {str(e)}"}), 500

@tenant_bp.route('/tenants/<int:tenant_id>/invite', methods=['POST'])
@jwt_required()
@audit_log(action="invite_user", resource_type="tenant")
def invite_user_to_tenant(tenant_id):
    """邀請使用者加入租戶"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return jsonify({"message": "租戶不存在"}), 404
    
    # 檢查權限：租戶擁有者或管理員
    if not (user.tenant_id == tenant_id and user.tenant_role in ['owner', 'admin']):
        return jsonify({"message": "權限不足"}), 403
    
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'member')
    
    if not email:
        return jsonify({"message": "電子郵件為必填欄位"}), 400
    
    if role not in ['member', 'admin']:
        return jsonify({"message": "無效的角色"}), 400
    
    # 檢查是否可以新增使用者
    if not tenant.can_add_user():
        return jsonify({"message": "已達到使用者數量上限"}), 400
    
    # 檢查使用者是否已存在於租戶中
    existing_user = User.query.filter_by(email=email, tenant_id=tenant_id).first()
    if existing_user:
        return jsonify({"message": "使用者已在此租戶中"}), 400
    
    # 檢查是否已有未處理的邀請
    existing_invitation = TenantInvitation.query.filter_by(
        tenant_id=tenant_id,
        email=email,
        is_accepted=False,
        is_expired=False
    ).first()
    
    if existing_invitation and existing_invitation.is_valid():
        return jsonify({"message": "已有未處理的邀請"}), 400
    
    try:
        # 建立邀請
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            token=secrets.token_urlsafe(32),
            invited_by_user_id=current_user_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.session.add(invitation)
        db.session.commit()
        
        # TODO: 發送邀請郵件
        
        return jsonify({
            "message": "邀請已發送",
            "invitation": invitation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"發送邀請失敗: {str(e)}"}), 500

@tenant_bp.route('/tenants/invitations/<token>/accept', methods=['POST'])
@jwt_required()
@audit_log(action="accept_invitation", resource_type="tenant")
def accept_invitation(token):
    """接受租戶邀請"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    invitation = TenantInvitation.get_by_token(token)
    if not invitation:
        return jsonify({"message": "邀請不存在或已失效"}), 404
    
    if not invitation.is_valid():
        return jsonify({"message": "邀請已過期或無效"}), 400
    
    # 檢查邀請的電子郵件是否與當前使用者匹配
    if invitation.email != user.email:
        return jsonify({"message": "邀請電子郵件與當前使用者不符"}), 400
    
    # 檢查使用者是否已屬於其他租戶
    if user.tenant_id:
        return jsonify({"message": "使用者已屬於其他租戶"}), 400
    
    try:
        # 接受邀請
        user.tenant_id = invitation.tenant_id
        user.tenant_role = invitation.role
        
        invitation.is_accepted = True
        invitation.accepted_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "邀請接受成功",
            "tenant": invitation.tenant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"接受邀請失敗: {str(e)}"}), 500

@tenant_bp.route('/tenants/<int:tenant_id>/members', methods=['GET'])
@jwt_required()
@audit_log(action="list_members", resource_type="tenant")
def list_tenant_members(tenant_id):
    """列出租戶成員"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return jsonify({"message": "租戶不存在"}), 404
    
    # 檢查權限：租戶成員
    if user.tenant_id != tenant_id:
        return jsonify({"message": "權限不足"}), 403
    
    members = User.query.filter_by(tenant_id=tenant_id).all()
    
    return jsonify({
        "members": [{
            "id": member.id,
            "username": member.username,
            "email": member.email,
            "tenant_role": member.tenant_role,
            "is_active": member.is_active,
            "created_at": member.created_at.isoformat() if member.created_at else None
        } for member in members]
    }), 200

@tenant_bp.route('/tenants/<int:tenant_id>/members/<int:user_id>', methods=['PUT'])
@jwt_required()
@audit_log(action="update_member", resource_type="tenant")
def update_tenant_member(tenant_id, user_id):
    """更新租戶成員角色"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({"message": "使用者不存在"}), 404
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return jsonify({"message": "租戶不存在"}), 404
    
    # 檢查權限：租戶擁有者或管理員
    if not (current_user.tenant_id == tenant_id and current_user.tenant_role in ['owner', 'admin']):
        return jsonify({"message": "權限不足"}), 403
    
    target_user = User.query.get(user_id)
    if not target_user or target_user.tenant_id != tenant_id:
        return jsonify({"message": "成員不存在"}), 404
    
    data = request.get_json()
    new_role = data.get('tenant_role')
    
    if new_role not in ['member', 'admin', 'owner']:
        return jsonify({"message": "無效的角色"}), 400
    
    # 不能修改自己的角色
    if target_user.id == current_user_id:
        return jsonify({"message": "不能修改自己的角色"}), 400
    
    # 只有擁有者可以設定其他擁有者
    if new_role == 'owner' and current_user.tenant_role != 'owner':
        return jsonify({"message": "只有擁有者可以設定其他擁有者"}), 403
    
    try:
        target_user.tenant_role = new_role
        db.session.commit()
        
        return jsonify({
            "message": "成員角色更新成功",
            "user": {
                "id": target_user.id,
                "username": target_user.username,
                "email": target_user.email,
                "tenant_role": target_user.tenant_role
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"更新成員角色失敗: {str(e)}"}), 500
