#!/usr/bin/env python3
"""
監控基線配置 - 5 個核心指標（QPS、p95 延遲、錯誤率、隊列滯留、外部調用失敗率）+ 基本告警
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
import statistics

# 配置結構化日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)

class MetricsCollector:
    """核心指標收集器"""
    
    def __init__(self, window_size_minutes=5):
        self.window_size = window_size_minutes * 60  # 轉換為秒
        self.logger = logging.getLogger(__name__)
        
        # 指標數據存儲（使用 deque 實現滑動窗口）
        self.request_times = deque()  # (timestamp, response_time, status_code, endpoint)
        self.external_calls = deque()  # (timestamp, success, service_name, response_time)
        self.queue_metrics = deque()  # (timestamp, queue_size, queue_name)
        
        # 告警閾值配置
        self.thresholds = {
            'qps_max': 100,  # 最大 QPS
            'p95_latency_ms': 2000,  # P95 延遲閾值（毫秒）
            'error_rate_percent': 5.0,  # 錯誤率閾值（百分比）
            'queue_size_max': 1000,  # 隊列最大大小
            'external_failure_rate_percent': 10.0  # 外部調用失敗率閾值
        }
        
        # 告警狀態追蹤
        self.alert_states = defaultdict(bool)
        self.last_alert_times = defaultdict(lambda: datetime.min)
        self.alert_cooldown_minutes = 5  # 告警冷卻時間
        
        # 啟動後台監控線程
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("MetricsCollector initialized with window size: %d seconds", self.window_size)
    
    def record_request(self, response_time_ms: float, status_code: int, endpoint: str = "unknown"):
        """記錄請求指標"""
        timestamp = time.time()
        self.request_times.append((timestamp, response_time_ms, status_code, endpoint))
        self._cleanup_old_data()
        
        # 結構化日誌
        self.logger.info(
            "Request recorded",
            extra={
                "metric_type": "request",
                "response_time_ms": response_time_ms,
                "status_code": status_code,
                "endpoint": endpoint,
                "timestamp": timestamp
            }
        )
    
    def record_external_call(self, success: bool, service_name: str, response_time_ms: float = 0):
        """記錄外部調用指標"""
        timestamp = time.time()
        self.external_calls.append((timestamp, success, service_name, response_time_ms))
        self._cleanup_old_data()
        
        self.logger.info(
            "External call recorded",
            extra={
                "metric_type": "external_call",
                "success": success,
                "service_name": service_name,
                "response_time_ms": response_time_ms,
                "timestamp": timestamp
            }
        )
    
    def record_queue_size(self, queue_size: int, queue_name: str = "default"):
        """記錄隊列大小指標"""
        timestamp = time.time()
        self.queue_metrics.append((timestamp, queue_size, queue_name))
        self._cleanup_old_data()
        
        self.logger.info(
            "Queue size recorded",
            extra={
                "metric_type": "queue_size",
                "queue_size": queue_size,
                "queue_name": queue_name,
                "timestamp": timestamp
            }
        )
    
    def _cleanup_old_data(self):
        """清理超出時間窗口的舊數據"""
        cutoff_time = time.time() - self.window_size
        
        while self.request_times and self.request_times[0][0] < cutoff_time:
            self.request_times.popleft()
            
        while self.external_calls and self.external_calls[0][0] < cutoff_time:
            self.external_calls.popleft()
            
        while self.queue_metrics and self.queue_metrics[0][0] < cutoff_time:
            self.queue_metrics.popleft()
    
    def get_qps(self) -> float:
        """計算當前 QPS（每秒請求數）"""
        if not self.request_times:
            return 0.0
        
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # 計算時間窗口內的請求數
        requests_in_window = sum(1 for timestamp, _, _, _ in self.request_times if timestamp >= window_start)
        
        # 計算實際時間窗口大小（可能小於配置的窗口大小）
        actual_window = min(self.window_size, current_time - self.request_times[0][0]) if self.request_times else self.window_size
        
        return requests_in_window / actual_window if actual_window > 0 else 0.0
    
    def get_p95_latency(self) -> float:
        """計算 P95 延遲（毫秒）"""
        if not self.request_times:
            return 0.0
        
        response_times = [response_time for _, response_time, _, _ in self.request_times]
        
        if len(response_times) < 2:
            return response_times[0] if response_times else 0.0
        
        return statistics.quantiles(response_times, n=20)[18]  # P95 = 95th percentile
    
    def get_error_rate(self) -> float:
        """計算錯誤率（百分比）"""
        if not self.request_times:
            return 0.0
        
        total_requests = len(self.request_times)
        error_requests = sum(1 for _, _, status_code, _ in self.request_times if status_code >= 400)
        
        return (error_requests / total_requests) * 100 if total_requests > 0 else 0.0
    
    def get_max_queue_size(self) -> int:
        """獲取最大隊列大小"""
        if not self.queue_metrics:
            return 0
        
        return max(queue_size for _, queue_size, _ in self.queue_metrics)
    
    def get_external_failure_rate(self) -> float:
        """計算外部調用失敗率（百分比）"""
        if not self.external_calls:
            return 0.0
        
        total_calls = len(self.external_calls)
        failed_calls = sum(1 for _, success, _, _ in self.external_calls if not success)
        
        return (failed_calls / total_calls) * 100 if total_calls > 0 else 0.0
    
    def get_all_metrics(self) -> Dict:
        """獲取所有核心指標"""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "qps": round(self.get_qps(), 2),
            "p95_latency_ms": round(self.get_p95_latency(), 2),
            "error_rate_percent": round(self.get_error_rate(), 2),
            "max_queue_size": self.get_max_queue_size(),
            "external_failure_rate_percent": round(self.get_external_failure_rate(), 2),
            "window_size_seconds": self.window_size,
            "data_points": {
                "requests": len(self.request_times),
                "external_calls": len(self.external_calls),
                "queue_metrics": len(self.queue_metrics)
            }
        }
    
    def check_alerts(self) -> List[Dict]:
        """檢查告警條件"""
        alerts = []
        current_time = datetime.utcnow()
        
        # 檢查各項指標是否超過閾值
        metrics = self.get_all_metrics()
        
        alert_checks = [
            ("high_qps", metrics["qps"] > self.thresholds["qps_max"], 
             f"QPS過高: {metrics['qps']:.2f} > {self.thresholds['qps_max']}"),
            ("high_latency", metrics["p95_latency_ms"] > self.thresholds["p95_latency_ms"],
             f"P95延遲過高: {metrics['p95_latency_ms']:.2f}ms > {self.thresholds['p95_latency_ms']}ms"),
            ("high_error_rate", metrics["error_rate_percent"] > self.thresholds["error_rate_percent"],
             f"錯誤率過高: {metrics['error_rate_percent']:.2f}% > {self.thresholds['error_rate_percent']}%"),
            ("large_queue", metrics["max_queue_size"] > self.thresholds["queue_size_max"],
             f"隊列過大: {metrics['max_queue_size']} > {self.thresholds['queue_size_max']}"),
            ("high_external_failure", metrics["external_failure_rate_percent"] > self.thresholds["external_failure_rate_percent"],
             f"外部調用失敗率過高: {metrics['external_failure_rate_percent']:.2f}% > {self.thresholds['external_failure_rate_percent']}%")
        ]
        
        for alert_type, condition, message in alert_checks:
            if condition:
                # 檢查告警冷卻時間
                last_alert = self.last_alert_times[alert_type]
                if (current_time - last_alert).total_seconds() > self.alert_cooldown_minutes * 60:
                    alert = {
                        "type": alert_type,
                        "message": message,
                        "timestamp": current_time.isoformat() + "Z",
                        "severity": "warning",
                        "metrics": metrics
                    }
                    alerts.append(alert)
                    self.last_alert_times[alert_type] = current_time
                    self.alert_states[alert_type] = True
                    
                    # 記錄告警日誌
                    self.logger.warning(
                        f"Alert triggered: {alert_type} - {message}",
                        extra={
                            "alert_type": alert_type,
                            "alert_message": message,
                            "metrics": metrics
                        }
                    )
            else:
                # 重置告警狀態
                if self.alert_states[alert_type]:
                    self.alert_states[alert_type] = False
                    self.logger.info(f"Alert resolved: {alert_type}")
        
        return alerts
    
    def _monitoring_loop(self):
        """後台監控循環"""
        while True:
            try:
                # 每分鐘檢查一次告警
                time.sleep(60)
                
                # 清理舊數據
                self._cleanup_old_data()
                
                # 檢查告警
                alerts = self.check_alerts()
                
                # 記錄當前指標
                metrics = self.get_all_metrics()
                self.logger.info(
                    "Metrics snapshot",
                    extra={
                        "metric_type": "snapshot",
                        "metrics": metrics,
                        "active_alerts": len(alerts)
                    }
                )
                
                # 如果有告警，可以在這裡添加通知邏輯
                # 例如：發送郵件、Slack 通知、webhook 等
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

# 全局指標收集器實例
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """獲取全局指標收集器實例"""
    return metrics_collector

# Flask 中間件示例
def flask_metrics_middleware(app):
    """Flask 應用程式的指標收集中間件"""
    
    @app.before_request
    def before_request():
        import flask
        flask.g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        import flask
        if hasattr(flask.g, 'start_time'):
            response_time_ms = (time.time() - flask.g.start_time) * 1000
            endpoint = flask.request.endpoint or flask.request.path
            
            metrics_collector.record_request(
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                endpoint=endpoint
            )
        
        return response
    
    return app

# 使用示例
if __name__ == "__main__":
    # 模擬一些指標數據
    import random
    
    print("模擬指標收集...")
    
    for i in range(100):
        # 模擬請求
        response_time = random.uniform(50, 500)
        status_code = random.choice([200, 200, 200, 200, 404, 500])  # 大部分成功
        metrics_collector.record_request(response_time, status_code, f"/api/endpoint{i%5}")
        
        # 模擬外部調用
        success = random.choice([True, True, True, False])  # 75% 成功率
        metrics_collector.record_external_call(success, "database", random.uniform(10, 100))
        
        # 模擬隊列大小
        queue_size = random.randint(0, 50)
        metrics_collector.record_queue_size(queue_size, "task_queue")
        
        time.sleep(0.1)  # 模擬時間間隔
    
    # 輸出當前指標
    print("\n當前指標:")
    print(json.dumps(metrics_collector.get_all_metrics(), indent=2, ensure_ascii=False))
    
    # 檢查告警
    alerts = metrics_collector.check_alerts()
    if alerts:
        print(f"\n發現 {len(alerts)} 個告警:")
        for alert in alerts:
            print(f"- {alert['type']}: {alert['message']}")
    else:
        print("\n✅ 所有指標正常，無告警")
