"""
監控持續化系統
提供健康檢查輪詢、告警通知和狀態追蹤
"""

import asyncio
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import aiohttp
import requests
from dataclasses import dataclass, asdict

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """健康檢查結果"""
    service_name: str
    url: str
    status_code: int
    response_time: float
    is_healthy: bool
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class AlertConfig:
    """告警配置"""
    enabled: bool = True
    email_recipients: List[str] = None
    webhook_url: Optional[str] = None
    slack_webhook: Optional[str] = None
    failure_threshold: int = 3  # 連續失敗次數觸發告警
    recovery_notification: bool = True
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

class ContinuousMonitor:
    """持續監控系統"""
    
    def __init__(self, config_file: str = None):
        self.services = {}
        self.alert_config = AlertConfig()
        self.failure_counts = {}
        self.last_alert_times = {}
        self.monitoring_active = False
        self.results_history = []
        
        # 載入配置
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        else:
            self.setup_default_config()
    
    def setup_default_config(self):
        """設置預設監控配置"""
        # MorningAI MVP 服務端點
        self.services = {
            'backend_health': {
                'url': 'https://morningai-mvp.onrender.com/health',
                'method': 'GET',
                'timeout': 30,
                'expected_status': 200,
                'check_interval': 60,  # 每分鐘檢查
                'critical': True
            },
            'backend_api': {
                'url': 'https://morningai-mvp.onrender.com/api/swagger.json',
                'method': 'GET',
                'timeout': 15,
                'expected_status': 200,
                'check_interval': 300,  # 每5分鐘檢查
                'critical': False
            },
            'frontend_app': {
                'url': 'https://morningai-mvp-web.vercel.app',
                'method': 'GET',
                'timeout': 15,
                'expected_status': 200,
                'check_interval': 300,  # 每5分鐘檢查
                'critical': True
            },
            'docs_endpoint': {
                'url': 'https://morningai-mvp.onrender.com/docs/',
                'method': 'GET',
                'timeout': 15,
                'expected_status': 200,
                'check_interval': 600,  # 每10分鐘檢查
                'critical': False
            }
        }
        
        # 告警配置
        self.alert_config = AlertConfig(
            enabled=True,
            email_recipients=os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(','),
            webhook_url=os.getenv('ALERT_WEBHOOK_URL'),
            slack_webhook=os.getenv('SLACK_WEBHOOK_URL'),
            failure_threshold=3,
            recovery_notification=True
        )
    
    def load_config(self, config_file: str):
        """從檔案載入監控配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.services = config.get('services', {})
            alert_data = config.get('alert_config', {})
            self.alert_config = AlertConfig(**alert_data)
            
            logger.info(f"已載入監控配置：{len(self.services)} 個服務")
        except Exception as e:
            logger.error(f"載入配置失敗：{e}")
            self.setup_default_config()
    
    def save_config(self, config_file: str):
        """儲存監控配置到檔案"""
        try:
            config = {
                'services': self.services,
                'alert_config': asdict(self.alert_config)
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"監控配置已儲存到：{config_file}")
        except Exception as e:
            logger.error(f"儲存配置失敗：{e}")
    
    async def check_service_health(self, service_name: str, service_config: Dict) -> HealthCheckResult:
        """檢查單一服務健康狀態"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=service_config.get('timeout', 30))
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                method = service_config.get('method', 'GET').upper()
                
                if method == 'GET':
                    async with session.get(service_config['url']) as response:
                        status_code = response.status
                        response_time = time.time() - start_time
                        
                        # 檢查狀態碼
                        expected_status = service_config.get('expected_status', 200)
                        is_healthy = status_code == expected_status
                        
                        return HealthCheckResult(
                            service_name=service_name,
                            url=service_config['url'],
                            status_code=status_code,
                            response_time=response_time,
                            is_healthy=is_healthy,
                            error_message=None if is_healthy else f"Expected {expected_status}, got {status_code}"
                        )
                
                elif method == 'POST':
                    data = service_config.get('data', {})
                    async with session.post(service_config['url'], json=data) as response:
                        status_code = response.status
                        response_time = time.time() - start_time
                        
                        expected_status = service_config.get('expected_status', 200)
                        is_healthy = status_code == expected_status
                        
                        return HealthCheckResult(
                            service_name=service_name,
                            url=service_config['url'],
                            status_code=status_code,
                            response_time=response_time,
                            is_healthy=is_healthy,
                            error_message=None if is_healthy else f"Expected {expected_status}, got {status_code}"
                        )
        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service_name=service_name,
                url=service_config['url'],
                status_code=0,
                response_time=response_time,
                is_healthy=False,
                error_message="Request timeout"
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service_name=service_name,
                url=service_config['url'],
                status_code=0,
                response_time=response_time,
                is_healthy=False,
                error_message=str(e)
            )
    
    async def run_health_checks(self) -> List[HealthCheckResult]:
        """執行所有服務的健康檢查"""
        tasks = []
        
        for service_name, service_config in self.services.items():
            task = self.check_service_health(service_name, service_config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.services.keys())[i]
                service_config = list(self.services.values())[i]
                
                processed_results.append(HealthCheckResult(
                    service_name=service_name,
                    url=service_config['url'],
                    status_code=0,
                    response_time=0,
                    is_healthy=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def update_failure_counts(self, results: List[HealthCheckResult]):
        """更新失敗計數"""
        for result in results:
            service_name = result.service_name
            
            if not result.is_healthy:
                self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
            else:
                # 服務恢復，重置失敗計數
                if service_name in self.failure_counts and self.failure_counts[service_name] > 0:
                    logger.info(f"服務 {service_name} 已恢復正常")
                    if self.alert_config.recovery_notification:
                        self.send_recovery_alert(result)
                
                self.failure_counts[service_name] = 0
    
    def should_send_alert(self, result: HealthCheckResult) -> bool:
        """判斷是否應該發送告警"""
        if not self.alert_config.enabled:
            return False
        
        service_name = result.service_name
        failure_count = self.failure_counts.get(service_name, 0)
        
        # 檢查是否達到失敗閾值
        if failure_count >= self.alert_config.failure_threshold:
            # 檢查是否在冷卻期內（避免重複告警）
            last_alert = self.last_alert_times.get(service_name)
            if last_alert:
                cooldown_period = timedelta(minutes=30)  # 30分鐘冷卻期
                if datetime.utcnow() - last_alert < cooldown_period:
                    return False
            
            return True
        
        return False
    
    def send_alert(self, result: HealthCheckResult):
        """發送告警通知"""
        try:
            service_name = result.service_name
            failure_count = self.failure_counts.get(service_name, 0)
            
            # 準備告警訊息
            alert_message = self.format_alert_message(result, failure_count)
            
            # 發送郵件告警
            if self.alert_config.email_recipients:
                self.send_email_alert(alert_message, result)
            
            # 發送 Webhook 告警
            if self.alert_config.webhook_url:
                self.send_webhook_alert(alert_message, result)
            
            # 發送 Slack 告警
            if self.alert_config.slack_webhook:
                self.send_slack_alert(alert_message, result)
            
            # 記錄告警時間
            self.last_alert_times[service_name] = datetime.utcnow()
            
            logger.warning(f"已發送告警：{service_name} - {result.error_message}")
        
        except Exception as e:
            logger.error(f"發送告警失敗：{e}")
    
    def send_recovery_alert(self, result: HealthCheckResult):
        """發送恢復通知"""
        try:
            recovery_message = f"""
🟢 服務恢復通知

服務名稱：{result.service_name}
服務 URL：{result.url}
當前狀態：正常 (HTTP {result.status_code})
回應時間：{result.response_time:.2f}s
恢復時間：{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC

服務已恢復正常運行。
            """.strip()
            
            # 發送恢復通知（簡化版）
            if self.alert_config.email_recipients:
                self.send_email_alert(recovery_message, result, is_recovery=True)
            
            logger.info(f"已發送恢復通知：{result.service_name}")
        
        except Exception as e:
            logger.error(f"發送恢復通知失敗：{e}")
    
    def format_alert_message(self, result: HealthCheckResult, failure_count: int) -> str:
        """格式化告警訊息"""
        service_config = self.services.get(result.service_name, {})
        is_critical = service_config.get('critical', False)
        
        severity = "🔴 嚴重" if is_critical else "🟡 警告"
        
        message = f"""
{severity} 服務異常告警

服務名稱：{result.service_name}
服務 URL：{result.url}
錯誤狀態：HTTP {result.status_code}
錯誤訊息：{result.error_message}
回應時間：{result.response_time:.2f}s
連續失敗：{failure_count} 次
檢查時間：{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC

請立即檢查服務狀態並進行修復。
        """.strip()
        
        return message
    
    def send_email_alert(self, message: str, result: HealthCheckResult, is_recovery: bool = False):
        """發送郵件告警"""
        try:
            # 郵件配置
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_pass = os.getenv('SMTP_PASS')
            
            if not smtp_user or not smtp_pass:
                logger.warning("郵件配置不完整，跳過郵件告警")
                return
            
            # 創建郵件
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = ', '.join(self.alert_config.email_recipients)
            
            if is_recovery:
                msg['Subject'] = f"[MorningAI] 服務恢復 - {result.service_name}"
            else:
                msg['Subject'] = f"[MorningAI] 服務告警 - {result.service_name}"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 發送郵件
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            logger.info(f"郵件告警已發送到：{self.alert_config.email_recipients}")
        
        except Exception as e:
            logger.error(f"發送郵件告警失敗：{e}")
    
    def send_webhook_alert(self, message: str, result: HealthCheckResult):
        """發送 Webhook 告警"""
        try:
            payload = {
                'service_name': result.service_name,
                'url': result.url,
                'status_code': result.status_code,
                'error_message': result.error_message,
                'response_time': result.response_time,
                'timestamp': result.timestamp.isoformat(),
                'message': message
            }
            
            response = requests.post(
                self.alert_config.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Webhook 告警已發送")
            else:
                logger.warning(f"Webhook 告警發送失敗：{response.status_code}")
        
        except Exception as e:
            logger.error(f"發送 Webhook 告警失敗：{e}")
    
    def send_slack_alert(self, message: str, result: HealthCheckResult):
        """發送 Slack 告警"""
        try:
            payload = {
                'text': f"MorningAI 監控告警",
                'attachments': [
                    {
                        'color': 'danger' if not result.is_healthy else 'good',
                        'fields': [
                            {
                                'title': '服務名稱',
                                'value': result.service_name,
                                'short': True
                            },
                            {
                                'title': '狀態碼',
                                'value': str(result.status_code),
                                'short': True
                            },
                            {
                                'title': '錯誤訊息',
                                'value': result.error_message or 'N/A',
                                'short': False
                            }
                        ],
                        'ts': int(result.timestamp.timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.alert_config.slack_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack 告警已發送")
            else:
                logger.warning(f"Slack 告警發送失敗：{response.status_code}")
        
        except Exception as e:
            logger.error(f"發送 Slack 告警失敗：{e}")
    
    def get_monitoring_status(self) -> Dict:
        """獲取監控狀態摘要"""
        total_services = len(self.services)
        failed_services = sum(1 for count in self.failure_counts.values() if count > 0)
        healthy_services = total_services - failed_services
        
        return {
            'monitoring_active': self.monitoring_active,
            'total_services': total_services,
            'healthy_services': healthy_services,
            'failed_services': failed_services,
            'failure_counts': dict(self.failure_counts),
            'last_check': datetime.utcnow().isoformat(),
            'alert_config': asdict(self.alert_config)
        }
    
    async def start_monitoring(self):
        """啟動持續監控"""
        self.monitoring_active = True
        logger.info("開始持續監控...")
        
        try:
            while self.monitoring_active:
                # 執行健康檢查
                results = await self.run_health_checks()
                
                # 更新失敗計數
                self.update_failure_counts(results)
                
                # 檢查是否需要發送告警
                for result in results:
                    if not result.is_healthy and self.should_send_alert(result):
                        self.send_alert(result)
                
                # 儲存結果歷史
                self.results_history.extend(results)
                
                # 保持最近 1000 筆記錄
                if len(self.results_history) > 1000:
                    self.results_history = self.results_history[-1000:]
                
                # 記錄監控狀態
                status = self.get_monitoring_status()
                logger.info(f"監控狀態：{status['healthy_services']}/{status['total_services']} 服務正常")
                
                # 等待下次檢查
                await asyncio.sleep(60)  # 每分鐘執行一次主循環
        
        except Exception as e:
            logger.error(f"監控過程發生錯誤：{e}")
        finally:
            self.monitoring_active = False
            logger.info("監控已停止")
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        logger.info("正在停止監控...")

# 獨立運行的監控腳本
async def main():
    """主函數"""
    monitor = ContinuousMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在停止監控...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
