import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import sessionmaker
from celery import Celery

from src.database import db
from src.models.webhook import Webhook, WebhookDelivery, WebhookEvent, WEBHOOK_EVENTS

# 設定日誌
logger = logging.getLogger(__name__)

# Celery 配置 (用於非同步處理)
celery_app = Celery('webhook_service')

class WebhookService:
    """
    Webhook 服務類別 - 處理 webhook 的觸發和傳送
    """
    
    def __init__(self):
        self.session = db.session
    
    def create_webhook(self, tenant_id: Optional[int], name: str, url: str, 
                      events: List[str], secret: Optional[str] = None,
                      max_retries: int = 3, retry_delay: int = 60) -> Webhook:
        """建立新的 webhook"""
        
        # 驗證事件類型
        invalid_events = [event for event in events if event not in WEBHOOK_EVENTS]
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}")
        
        webhook = Webhook(
            tenant_id=tenant_id,
            name=name,
            url=url,
            events=events,
            secret=secret,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        self.session.add(webhook)
        self.session.commit()
        
        logger.info(f"Created webhook {webhook.id} for tenant {tenant_id}")
        return webhook
    
    def update_webhook(self, webhook_id: int, **kwargs) -> Optional[Webhook]:
        """更新 webhook"""
        webhook = Webhook.query.get(webhook_id)
        if not webhook:
            return None
        
        # 更新允許的欄位
        allowed_fields = ['name', 'url', 'events', 'secret', 'is_active', 'max_retries', 'retry_delay']
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'events':
                    # 驗證事件類型
                    invalid_events = [event for event in value if event not in WEBHOOK_EVENTS]
                    if invalid_events:
                        raise ValueError(f"Invalid event types: {invalid_events}")
                
                setattr(webhook, field, value)
        
        webhook.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"Updated webhook {webhook_id}")
        return webhook
    
    def delete_webhook(self, webhook_id: int) -> bool:
        """刪除 webhook"""
        webhook = Webhook.query.get(webhook_id)
        if not webhook:
            return False
        
        self.session.delete(webhook)
        self.session.commit()
        
        logger.info(f"Deleted webhook {webhook_id}")
        return True
    
    def trigger_event(self, event_type: str, event_data: Dict, 
                     tenant_id: Optional[int] = None, 
                     triggered_by_user_id: Optional[int] = None,
                     source: Optional[str] = None) -> WebhookEvent:
        """觸發事件並處理相關的 webhooks"""
        
        if event_type not in WEBHOOK_EVENTS:
            raise ValueError(f"Invalid event type: {event_type}")
        
        # 建立事件記錄
        event = WebhookEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data,
            triggered_by_user_id=triggered_by_user_id,
            source=source
        )
        
        self.session.add(event)
        self.session.flush()  # 取得 event.id
        
        # 找到需要觸發的 webhooks
        query = Webhook.query.filter(Webhook.is_active == True)
        
        # 如果是租戶特定事件，只觸發該租戶的 webhooks 和全域 webhooks
        if tenant_id:
            query = query.filter(
                (Webhook.tenant_id == tenant_id) | (Webhook.tenant_id == None)
            )
        else:
            # 全域事件只觸發全域 webhooks
            query = query.filter(Webhook.tenant_id == None)
        
        webhooks = query.all()
        
        # 篩選出監聽此事件類型的 webhooks
        triggered_webhooks = [
            webhook for webhook in webhooks 
            if webhook.should_trigger_for_event(event_type)
        ]
        
        logger.info(f"Event {event_type} triggered {len(triggered_webhooks)} webhooks")
        
        # 非同步處理 webhook 傳送
        for webhook in triggered_webhooks:
            self._schedule_webhook_delivery(webhook, event)
        
        event.processed_at = datetime.utcnow()
        self.session.commit()
        
        return event
    
    def _schedule_webhook_delivery(self, webhook: Webhook, event: WebhookEvent):
        """安排 webhook 傳送"""
        
        # 準備 payload
        payload = {
            'event': {
                'id': event.id,
                'type': event.event_type,
                'created_at': event.created_at.isoformat(),
                'data': event.event_data
            },
            'tenant_id': event.tenant_id,
            'triggered_by_user_id': event.triggered_by_user_id,
            'source': event.source
        }
        
        payload_json = json.dumps(payload, ensure_ascii=False)
        
        # 建立傳送記錄
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event.event_type,
            payload=payload_json,
            max_attempts=webhook.max_retries + 1  # 包含初始嘗試
        )
        
        self.session.add(delivery)
        self.session.flush()  # 取得 delivery.id
        
        # 更新 webhook 統計
        webhook.total_calls += 1
        
        # 使用 Celery 非同步處理
        deliver_webhook_task.delay(delivery.id)
        
        logger.info(f"Scheduled webhook delivery {delivery.id} for webhook {webhook.id}")
    
    def deliver_webhook_sync(self, delivery_id: int) -> bool:
        """同步傳送 webhook (用於測試或立即傳送)"""
        delivery = WebhookDelivery.query.get(delivery_id)
        if not delivery:
            logger.error(f"Webhook delivery {delivery_id} not found")
            return False
        
        return self._execute_webhook_delivery(delivery)
    
    def _execute_webhook_delivery(self, delivery: WebhookDelivery) -> bool:
        """執行 webhook 傳送"""
        webhook = delivery.webhook
        
        try:
            # 準備請求標頭
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'MorningAI-Webhook/1.0',
                'X-Webhook-Event': delivery.event_type,
                'X-Webhook-Delivery': str(delivery.id),
                'X-Webhook-Timestamp': str(int(datetime.utcnow().timestamp()))
            }
            
            # 添加簽名
            if webhook.secret:
                signature = webhook.generate_signature(delivery.payload)
                if signature:
                    headers['X-Webhook-Signature'] = signature
            
            delivery.request_headers = headers
            delivery.attempt_count += 1
            
            # 發送請求
            response = requests.post(
                webhook.url,
                data=delivery.payload,
                headers=headers,
                timeout=30,  # 30 秒超時
                allow_redirects=False
            )
            
            # 處理回應
            if 200 <= response.status_code < 300:
                delivery.mark_as_success(
                    response_status_code=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response.text[:1000]  # 限制回應內容長度
                )
                self.session.commit()
                
                logger.info(f"Webhook delivery {delivery.id} succeeded")
                return True
            else:
                error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                
                if delivery.can_retry():
                    delivery.schedule_retry()
                    self.session.commit()
                    
                    # 安排重試
                    deliver_webhook_task.apply_async(
                        args=[delivery.id],
                        eta=delivery.next_retry_at
                    )
                    
                    logger.warning(f"Webhook delivery {delivery.id} failed, scheduled retry")
                else:
                    delivery.mark_as_failed(
                        error_message=error_message,
                        response_status_code=response.status_code,
                        response_headers=dict(response.headers),
                        response_body=response.text[:1000]
                    )
                    self.session.commit()
                    
                    logger.error(f"Webhook delivery {delivery.id} failed permanently")
                
                return False
                
        except requests.exceptions.RequestException as e:
            error_message = f"Request failed: {str(e)}"
            
            if delivery.can_retry():
                delivery.schedule_retry()
                self.session.commit()
                
                # 安排重試
                deliver_webhook_task.apply_async(
                    args=[delivery.id],
                    eta=delivery.next_retry_at
                )
                
                logger.warning(f"Webhook delivery {delivery.id} failed with exception, scheduled retry: {e}")
            else:
                delivery.mark_as_failed(error_message=error_message)
                self.session.commit()
                
                logger.error(f"Webhook delivery {delivery.id} failed permanently with exception: {e}")
            
            return False
        
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            delivery.mark_as_failed(error_message=error_message)
            self.session.commit()
            
            logger.error(f"Webhook delivery {delivery.id} failed with unexpected error: {e}")
            return False
    
    def get_webhook_deliveries(self, webhook_id: int, limit: int = 50, offset: int = 0) -> List[WebhookDelivery]:
        """取得 webhook 傳送記錄"""
        return WebhookDelivery.query.filter_by(webhook_id=webhook_id)\
                                  .order_by(WebhookDelivery.created_at.desc())\
                                  .limit(limit)\
                                  .offset(offset)\
                                  .all()
    
    def get_webhook_stats(self, webhook_id: int, days: int = 30) -> Dict:
        """取得 webhook 統計資料"""
        webhook = Webhook.query.get(webhook_id)
        if not webhook:
            return {}
        
        since = datetime.utcnow() - timedelta(days=days)
        
        deliveries = WebhookDelivery.query.filter(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.created_at >= since
        ).all()
        
        total = len(deliveries)
        successful = len([d for d in deliveries if d.status == 'success'])
        failed = len([d for d in deliveries if d.status == 'failed'])
        pending = len([d for d in deliveries if d.status in ['pending', 'retrying']])
        
        return {
            'total_deliveries': total,
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'pending_deliveries': pending,
            'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
            'average_response_time': 0,  # TODO: 實作回應時間統計
            'last_delivery_at': max([d.created_at for d in deliveries]).isoformat() if deliveries else None
        }
    
    def retry_failed_deliveries(self, webhook_id: Optional[int] = None, limit: int = 100):
        """重試失敗的傳送"""
        query = WebhookDelivery.query.filter(
            WebhookDelivery.status == 'retrying',
            WebhookDelivery.next_retry_at <= datetime.utcnow()
        )
        
        if webhook_id:
            query = query.filter(WebhookDelivery.webhook_id == webhook_id)
        
        failed_deliveries = query.limit(limit).all()
        
        for delivery in failed_deliveries:
            deliver_webhook_task.delay(delivery.id)
        
        logger.info(f"Scheduled {len(failed_deliveries)} failed deliveries for retry")
        return len(failed_deliveries)


# Celery 任務
@celery_app.task(bind=True, max_retries=3)
def deliver_webhook_task(self, delivery_id: int):
    """Celery 任務：傳送 webhook"""
    try:
        service = WebhookService()
        success = service.deliver_webhook_sync(delivery_id)
        
        if not success:
            # 如果傳送失敗，任務也不需要重試，因為重試邏輯在 service 中處理
            pass
            
    except Exception as e:
        logger.error(f"Webhook delivery task failed for delivery {delivery_id}: {e}")
        raise self.retry(countdown=60, exc=e)


# 全域 webhook 服務實例
webhook_service = WebhookService()
