#!/usr/bin/env python3
"""
Flask 應用程式監控整合 - 將監控基線整合到現有的 Flask 應用程式中
"""

import time
import logging
from flask import g, request, current_app
from functools import wraps
import sys
import os

# 添加監控模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'monitoring'))

try:
    from metrics_config import get_metrics_collector
    metrics_collector = get_metrics_collector()
except ImportError:
    # 如果監控模組不可用，創建一個空的收集器
    class DummyMetricsCollector:
        def record_request(self, *args, **kwargs):
            pass
        def record_external_call(self, *args, **kwargs):
            pass
        def record_queue_size(self, *args, **kwargs):
            pass
        def get_all_metrics(self):
            return {"error": "Metrics collector not available"}
        def check_alerts(self):
            return []
    
    metrics_collector = DummyMetricsCollector()

def init_monitoring(app):
    """初始化 Flask 應用程式的監控功能"""
    
    @app.before_request
    def before_request():
        """請求開始時記錄時間"""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}-{id(request)}"
    
    @app.after_request
    def after_request(response):
        """請求結束時記錄指標"""
        if hasattr(g, 'start_time'):
            response_time_ms = (time.time() - g.start_time) * 1000
            endpoint = request.endpoint or request.path
            
            # 記錄請求指標
            metrics_collector.record_request(
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                endpoint=endpoint
            )
            
            # 添加響應頭用於追蹤
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
            response.headers['X-Response-Time'] = f"{response_time_ms:.2f}ms"
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """處理未捕獲的異常並記錄指標"""
        if hasattr(g, 'start_time'):
            response_time_ms = (time.time() - g.start_time) * 1000
            endpoint = request.endpoint or request.path
            
            # 記錄錯誤請求
            metrics_collector.record_request(
                response_time_ms=response_time_ms,
                status_code=500,
                endpoint=endpoint
            )
        
        # 記錄錯誤日誌
        current_app.logger.error(
            f"Unhandled exception: {str(e)}",
            extra={
                "request_id": getattr(g, 'request_id', 'unknown'),
                "endpoint": request.endpoint or request.path,
                "method": request.method,
                "url": request.url
            }
        )
        
        # 重新拋出異常讓 Flask 處理
        raise e
    
    # 添加監控端點
    @app.route('/api/metrics')
    def get_metrics():
        """獲取當前監控指標"""
        try:
            metrics = metrics_collector.get_all_metrics()
            return {"status": "success", "metrics": metrics}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500
    
    @app.route('/api/alerts')
    def get_alerts():
        """獲取當前告警"""
        try:
            alerts = metrics_collector.check_alerts()
            return {
                "status": "success", 
                "alerts": alerts,
                "alert_count": len(alerts)
            }, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500
    
    current_app.logger.info("Monitoring integration initialized")

def monitor_external_call(service_name: str):
    """裝飾器：監控外部調用"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                # 記錄失敗的外部調用
                current_app.logger.error(
                    f"External call failed: {service_name}",
                    extra={
                        "service_name": service_name,
                        "error": str(e),
                        "function": func.__name__
                    }
                )
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000
                metrics_collector.record_external_call(
                    success=success,
                    service_name=service_name,
                    response_time_ms=response_time_ms
                )
        
        return wrapper
    return decorator

def record_queue_metric(queue_name: str, queue_size: int):
    """記錄隊列指標的輔助函數"""
    metrics_collector.record_queue_size(queue_size, queue_name)

# 使用示例
def example_database_call():
    """示例：監控資料庫調用"""
    @monitor_external_call("database")
    def query_users():
        # 模擬資料庫查詢
        time.sleep(0.1)
        return {"users": []}
    
    return query_users()

def example_api_call():
    """示例：監控外部 API 調用"""
    @monitor_external_call("external_api")
    def call_third_party_api():
        import requests
        response = requests.get("https://api.example.com/data", timeout=5)
        return response.json()
    
    return call_third_party_api()

# 結構化日誌配置
def setup_structured_logging(app):
    """設置結構化日誌"""
    import logging.config
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'structured',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': 'app.log'
            }
        },
        'loggers': {
            '': {  # root logger
                'level': 'INFO',
                'handlers': ['console', 'file']
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    app.logger.info("Structured logging configured")

# 健康檢查增強
def enhanced_health_check():
    """增強的健康檢查，包含監控指標"""
    try:
        metrics = metrics_collector.get_all_metrics()
        alerts = metrics_collector.check_alerts()
        
        # 基本健康狀態
        health_status = {
            "status": "ok",
            "timestamp": metrics["timestamp"],
            "version": "1.0.4",
            "monitoring": {
                "metrics": metrics,
                "alerts": {
                    "count": len(alerts),
                    "active": [alert["type"] for alert in alerts]
                }
            }
        }
        
        # 如果有高嚴重度告警，標記為不健康
        critical_alerts = [alert for alert in alerts if alert.get("severity") == "critical"]
        if critical_alerts:
            health_status["status"] = "degraded"
            health_status["issues"] = [alert["message"] for alert in critical_alerts]
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": time.time()
        }
