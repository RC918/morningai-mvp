from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.database import db
from src.models.user import User
from src.models.webhook import Webhook, WebhookDelivery, WebhookEvent, WEBHOOK_EVENTS
from src.services.webhook_service import webhook_service
from src.audit_log import audit_log

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhooks', methods=['GET'])
@jwt_required()
@audit_log(action="list_webhooks", resource_type="webhook")
def list_webhooks():
    """列出 webhooks"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    # 系統管理員可以看到所有 webhooks
    if user.is_admin():
        webhooks = Webhook.query.all()
    else:
        # 一般使用者只能看到自己租戶的 webhooks
        if not user.tenant_id:
            return jsonify({"webhooks": []}), 200
        
        webhooks = Webhook.query.filter(
            (Webhook.tenant_id == user.tenant_id) | (Webhook.tenant_id == None)
        ).all()
    
    return jsonify({
        "webhooks": [webhook.to_dict() for webhook in webhooks]
    }), 200

@webhook_bp.route('/webhooks', methods=['POST'])
@jwt_required()
@audit_log(action="create_webhook", resource_type="webhook")
def create_webhook():
    """建立新的 webhook"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    data = request.get_json()
    
    # 驗證必填欄位
    required_fields = ['name', 'url', 'events']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"{field} 為必填欄位"}), 400
    
    # 驗證 URL 格式
    url = data['url']
    if not url.startswith(('http://', 'https://')):
        return jsonify({"message": "URL 必須以 http:// 或 https:// 開頭"}), 400
    
    # 驗證事件類型
    events = data['events']
    if not isinstance(events, list) or not events:
        return jsonify({"message": "events 必須是非空的陣列"}), 400
    
    invalid_events = [event for event in events if event not in WEBHOOK_EVENTS]
    if invalid_events:
        return jsonify({
            "message": f"無效的事件類型: {invalid_events}",
            "valid_events": list(WEBHOOK_EVENTS.keys())
        }), 400
    
    # 決定租戶 ID
    tenant_id = None
    if not user.is_admin():
        # 非管理員只能為自己的租戶建立 webhook
        tenant_id = user.tenant_id
        if not tenant_id:
            return jsonify({"message": "使用者必須屬於租戶才能建立 webhook"}), 400
    else:
        # 管理員可以指定租戶 ID 或建立全域 webhook
        tenant_id = data.get('tenant_id')
    
    try:
        webhook = webhook_service.create_webhook(
            tenant_id=tenant_id,
            name=data['name'],
            url=url,
            events=events,
            secret=data.get('secret'),
            max_retries=data.get('max_retries', 3),
            retry_delay=data.get('retry_delay', 60)
        )
        
        return jsonify({
            "message": "Webhook 建立成功",
            "webhook": webhook.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"建立 webhook 失敗: {str(e)}"}), 500

@webhook_bp.route('/webhooks/<int:webhook_id>', methods=['GET'])
@jwt_required()
@audit_log(action="get_webhook", resource_type="webhook")
def get_webhook(webhook_id):
    """取得 webhook 詳細資訊"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify({"message": "Webhook 不存在"}), 404
    
    # 檢查權限
    if not user.is_admin():
        if webhook.tenant_id != user.tenant_id:
            return jsonify({"message": "權限不足"}), 403
    
    webhook_data = webhook.to_dict()
    webhook_data['stats'] = webhook_service.get_webhook_stats(webhook_id)
    
    return jsonify({"webhook": webhook_data}), 200

@webhook_bp.route('/webhooks/<int:webhook_id>', methods=['PUT'])
@jwt_required()
@audit_log(action="update_webhook", resource_type="webhook")
def update_webhook(webhook_id):
    """更新 webhook"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify({"message": "Webhook 不存在"}), 404
    
    # 檢查權限
    if not user.is_admin():
        if webhook.tenant_id != user.tenant_id:
            return jsonify({"message": "權限不足"}), 403
    
    data = request.get_json()
    
    try:
        # 驗證事件類型 (如果有提供)
        if 'events' in data:
            events = data['events']
            if not isinstance(events, list) or not events:
                return jsonify({"message": "events 必須是非空的陣列"}), 400
            
            invalid_events = [event for event in events if event not in WEBHOOK_EVENTS]
            if invalid_events:
                return jsonify({
                    "message": f"無效的事件類型: {invalid_events}",
                    "valid_events": list(WEBHOOK_EVENTS.keys())
                }), 400
        
        # 驗證 URL 格式 (如果有提供)
        if 'url' in data:
            url = data['url']
            if not url.startswith(('http://', 'https://')):
                return jsonify({"message": "URL 必須以 http:// 或 https:// 開頭"}), 400
        
        updated_webhook = webhook_service.update_webhook(webhook_id, **data)
        
        if not updated_webhook:
            return jsonify({"message": "更新 webhook 失敗"}), 500
        
        return jsonify({
            "message": "Webhook 更新成功",
            "webhook": updated_webhook.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"更新 webhook 失敗: {str(e)}"}), 500

@webhook_bp.route('/webhooks/<int:webhook_id>', methods=['DELETE'])
@jwt_required()
@audit_log(action="delete_webhook", resource_type="webhook")
def delete_webhook(webhook_id):
    """刪除 webhook"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify({"message": "Webhook 不存在"}), 404
    
    # 檢查權限
    if not user.is_admin():
        if webhook.tenant_id != user.tenant_id:
            return jsonify({"message": "權限不足"}), 403
    
    try:
        success = webhook_service.delete_webhook(webhook_id)
        
        if success:
            return jsonify({"message": "Webhook 刪除成功"}), 200
        else:
            return jsonify({"message": "刪除 webhook 失敗"}), 500
            
    except Exception as e:
        return jsonify({"message": f"刪除 webhook 失敗: {str(e)}"}), 500

@webhook_bp.route('/webhooks/<int:webhook_id>/test', methods=['POST'])
@jwt_required()
@audit_log(action="test_webhook", resource_type="webhook")
def test_webhook(webhook_id):
    """測試 webhook"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify({"message": "Webhook 不存在"}), 404
    
    # 檢查權限
    if not user.is_admin():
        if webhook.tenant_id != user.tenant_id:
            return jsonify({"message": "權限不足"}), 403
    
    try:
        # 觸發測試事件
        test_event = webhook_service.trigger_event(
            event_type='system.webhook_test',
            event_data={
                'webhook_id': webhook_id,
                'test_timestamp': datetime.utcnow().isoformat(),
                'message': 'This is a test webhook delivery'
            },
            tenant_id=webhook.tenant_id,
            triggered_by_user_id=current_user_id,
            source='webhook_test'
        )
        
        return jsonify({
            "message": "測試 webhook 已觸發",
            "event_id": test_event.id
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"測試 webhook 失敗: {str(e)}"}), 500

@webhook_bp.route('/webhooks/<int:webhook_id>/deliveries', methods=['GET'])
@jwt_required()
@audit_log(action="list_webhook_deliveries", resource_type="webhook")
def list_webhook_deliveries(webhook_id):
    """列出 webhook 傳送記錄"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify({"message": "Webhook 不存在"}), 404
    
    # 檢查權限
    if not user.is_admin():
        if webhook.tenant_id != user.tenant_id:
            return jsonify({"message": "權限不足"}), 403
    
    # 分頁參數
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    
    deliveries = webhook_service.get_webhook_deliveries(webhook_id, limit, offset)
    
    return jsonify({
        "deliveries": [delivery.to_dict() for delivery in deliveries],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": len(deliveries) == limit
        }
    }), 200

@webhook_bp.route('/webhooks/<int:webhook_id>/deliveries/<int:delivery_id>/retry', methods=['POST'])
@jwt_required()
@audit_log(action="retry_webhook_delivery", resource_type="webhook")
def retry_webhook_delivery(webhook_id, delivery_id):
    """重試 webhook 傳送"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify({"message": "Webhook 不存在"}), 404
    
    # 檢查權限
    if not user.is_admin():
        if webhook.tenant_id != user.tenant_id:
            return jsonify({"message": "權限不足"}), 403
    
    delivery = WebhookDelivery.query.filter_by(
        id=delivery_id,
        webhook_id=webhook_id
    ).first()
    
    if not delivery:
        return jsonify({"message": "傳送記錄不存在"}), 404
    
    if delivery.status not in ['failed', 'retrying']:
        return jsonify({"message": "只能重試失敗的傳送"}), 400
    
    try:
        # 重置傳送狀態並安排重試
        delivery.status = 'retrying'
        delivery.next_retry_at = datetime.utcnow()
        delivery.error_message = None
        db.session.commit()
        
        # 立即執行重試
        success = webhook_service.deliver_webhook_sync(delivery_id)
        
        return jsonify({
            "message": "重試完成",
            "success": success,
            "delivery": delivery.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"重試失敗: {str(e)}"}), 500

@webhook_bp.route('/webhook-events', methods=['GET'])
@jwt_required()
@audit_log(action="list_webhook_events", resource_type="webhook")
def list_webhook_events():
    """列出可用的 webhook 事件類型"""
    return jsonify({
        "events": WEBHOOK_EVENTS
    }), 200

@webhook_bp.route('/webhook-events/recent', methods=['GET'])
@jwt_required()
@audit_log(action="list_recent_events", resource_type="webhook")
def list_recent_events():
    """列出最近的事件"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"message": "使用者不存在"}), 404
    
    # 分頁參數
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    
    query = WebhookEvent.query
    
    # 非管理員只能看到自己租戶的事件
    if not user.is_admin():
        if user.tenant_id:
            query = query.filter(
                (WebhookEvent.tenant_id == user.tenant_id) | 
                (WebhookEvent.tenant_id == None)
            )
        else:
            query = query.filter(WebhookEvent.tenant_id == None)
    
    events = query.order_by(WebhookEvent.created_at.desc())\
                  .limit(limit)\
                  .offset(offset)\
                  .all()
    
    return jsonify({
        "events": [event.to_dict() for event in events],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": len(events) == limit
        }
    }), 200
