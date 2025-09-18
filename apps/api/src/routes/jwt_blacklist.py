from flask import Blueprint, jsonify, request, current_app
from src.models.user import User
from src.models.jwt_blacklist import JWTBlacklist
from src.database import db
from src.decorators import token_required, require_role
import jwt
from datetime import datetime
import uuid

jwt_blacklist_bp = Blueprint('jwt_blacklist', __name__)

def get_jti_from_token(token):
    """從 JWT token 中提取 JTI"""
    try:
        # 解碼 token 但不驗證簽名（因為我們只需要 JTI）
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        return unverified_payload.get('jti')
    except Exception:
        return None

@jwt_blacklist_bp.route('/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用戶登出，將 token 加入黑名單"""
    try:
        # 從 Authorization header 獲取 token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': '缺少授權標頭'}), 401
        
        token = auth_header.split(' ')[1]  # Bearer <token>
        
        # 解碼 token 獲取過期時間和 JTI
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            jti = payload.get('jti')
            exp = payload.get('exp')
            
            if not jti:
                # 如果 token 沒有 JTI，我們無法將其加入黑名單
                return jsonify({'message': '登出成功（token 無 JTI）'}), 200
            
            if exp:
                expires_at = datetime.fromtimestamp(exp)
            else:
                # 如果沒有過期時間，設置一個默認的過期時間
                expires_at = datetime.utcnow().replace(hour=23, minute=59, second=59)
            
            # 將 token 加入黑名單
            JWTBlacklist.add_to_blacklist(
                jti=jti,
                user_id=current_user.id,
                expires_at=expires_at,
                reason='logout'
            )
            
            return jsonify({'message': '登出成功'}), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '登出成功（token 已過期）'}), 200
        except jwt.InvalidTokenError:
            return jsonify({'message': '登出成功（token 無效）'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'message': '登出失敗'}), 500

@jwt_blacklist_bp.route('/auth/logout-all', methods=['POST'])
@token_required
def logout_all(current_user):
    """登出所有設備，撤銷用戶的所有 token"""
    try:
        # 在實際應用中，這裡應該實現撤銷用戶所有 token 的邏輯
        # 一種方法是在用戶表中添加 token_version 字段
        # 另一種方法是維護一個活躍 token 列表
        
        # 目前的實現：將當前 token 加入黑名單
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(' ')[1]
            
            try:
                payload = jwt.decode(
                    token,
                    current_app.config['JWT_SECRET_KEY'],
                    algorithms=['HS256']
                )
                
                jti = payload.get('jti')
                exp = payload.get('exp')
                
                if jti and exp:
                    expires_at = datetime.fromtimestamp(exp)
                    JWTBlacklist.add_to_blacklist(
                        jti=jti,
                        user_id=current_user.id,
                        expires_at=expires_at,
                        reason='logout_all'
                    )
            except:
                pass
        
        return jsonify({'message': '已登出所有設備'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout all error: {str(e)}")
        return jsonify({'message': '登出失敗'}), 500

@jwt_blacklist_bp.route('/auth/revoke-token', methods=['POST'])
@token_required
def revoke_token(current_user):
    """撤銷指定的 token"""
    try:
        data = request.get_json()
        token_to_revoke = data.get('token')
        reason = data.get('reason', 'manual_revoke')
        
        if not token_to_revoke:
            return jsonify({'message': '缺少要撤銷的 token'}), 400
        
        try:
            payload = jwt.decode(
                token_to_revoke,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            jti = payload.get('jti')
            exp = payload.get('exp')
            token_user_id = payload.get('user_id')
            
            # 檢查權限：只能撤銷自己的 token 或管理員可以撤銷任何 token
            if token_user_id != current_user.id and not current_user.is_admin():
                return jsonify({'message': '無權限撤銷此 token'}), 403
            
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp)
                JWTBlacklist.add_to_blacklist(
                    jti=jti,
                    user_id=token_user_id,
                    expires_at=expires_at,
                    reason=reason
                )
                
                return jsonify({'message': 'Token 已撤銷'}), 200
            else:
                return jsonify({'message': 'Token 格式無效'}), 400
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token 已過期'}), 400
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token 無效'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Revoke token error: {str(e)}")
        return jsonify({'message': 'Token 撤銷失敗'}), 500

@jwt_blacklist_bp.route('/admin/blacklist', methods=['GET'])
@require_role('admin')
def get_blacklist(current_user):
    """獲取黑名單列表（僅管理員）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 清理過期的 token
        JWTBlacklist.cleanup_expired_tokens()
        
        # 分頁查詢
        blacklist = JWTBlacklist.query.order_by(
            JWTBlacklist.blacklisted_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'blacklist': [token.to_dict() for token in blacklist.items],
            'total': blacklist.total,
            'pages': blacklist.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get blacklist error: {str(e)}")
        return jsonify({'message': '獲取黑名單失敗'}), 500

@jwt_blacklist_bp.route('/admin/blacklist/cleanup', methods=['POST'])
@require_role('admin')
def cleanup_blacklist(current_user):
    """清理過期的黑名單 token（僅管理員）"""
    try:
        cleaned_count = JWTBlacklist.cleanup_expired_tokens()
        return jsonify({
            'message': f'已清理 {cleaned_count} 個過期 token',
            'cleaned_count': cleaned_count
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Cleanup blacklist error: {str(e)}")
        return jsonify({'message': '清理黑名單失敗'}), 500

