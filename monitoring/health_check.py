#!/usr/bin/env python3
"""
MorningAI-MVP 健康檢查監控腳本
用於定期檢查應用程式健康狀態並記錄結果
"""

import json
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_check.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HealthChecker:
    """健康檢查器"""
    
    def __init__(self):
        self.endpoints = {
            'api': 'https://morningai-mvp.onrender.com/health',
            'web': 'https://morningai-mvp-web.vercel.app'
        }
        self.timeout = 10
        self.results = []
    
    def check_endpoint(self, name: str, url: str) -> Dict[str, Any]:
        """檢查單個端點的健康狀態"""
        start_time = time.time()
        result = {
            'name': name,
            'url': url,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'unknown',
            'response_time': 0,
            'status_code': None,
            'error': None
        }
        
        try:
            logger.info(f"檢查 {name} 端點: {url}")
            response = requests.get(url, timeout=self.timeout)
            
            result['response_time'] = round((time.time() - start_time) * 1000, 2)
            result['status_code'] = response.status_code
            
            if response.status_code == 200:
                result['status'] = 'healthy'
                logger.info(f"✅ {name} 健康 - {result['response_time']}ms")
                
                # 如果是 API 端點，檢查回應內容
                if name == 'api':
                    try:
                        data = response.json()
                        result['response_data'] = data
                        if data.get('status') != 'ok':
                            result['status'] = 'degraded'
                            result['error'] = f"API 回應狀態異常: {data.get('status')}"
                    except json.JSONDecodeError:
                        result['status'] = 'degraded'
                        result['error'] = "API 回應格式不正確"
            else:
                result['status'] = 'unhealthy'
                result['error'] = f"HTTP {response.status_code}"
                logger.warning(f"⚠️ {name} 不健康 - HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            result['response_time'] = self.timeout * 1000
            result['status'] = 'timeout'
            result['error'] = f"請求超時 (>{self.timeout}s)"
            logger.error(f"❌ {name} 超時")
            
        except requests.exceptions.ConnectionError:
            result['response_time'] = round((time.time() - start_time) * 1000, 2)
            result['status'] = 'connection_error'
            result['error'] = "連接錯誤"
            logger.error(f"❌ {name} 連接錯誤")
            
        except Exception as e:
            result['response_time'] = round((time.time() - start_time) * 1000, 2)
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"❌ {name} 檢查失敗: {e}")
        
        return result
    
    def run_health_check(self) -> Dict[str, Any]:
        """執行完整的健康檢查"""
        logger.info("開始健康檢查...")
        check_start = datetime.now(timezone.utc)
        
        endpoint_results = []
        for name, url in self.endpoints.items():
            result = self.check_endpoint(name, url)
            endpoint_results.append(result)
        
        # 計算整體狀態
        all_healthy = all(r['status'] == 'healthy' for r in endpoint_results)
        any_unhealthy = any(r['status'] in ['unhealthy', 'timeout', 'connection_error', 'error'] for r in endpoint_results)
        
        if all_healthy:
            overall_status = 'healthy'
        elif any_unhealthy:
            overall_status = 'unhealthy'
        else:
            overall_status = 'degraded'
        
        # 生成報告
        report = {
            'timestamp': check_start.isoformat(),
            'overall_status': overall_status,
            'endpoints': endpoint_results,
            'summary': {
                'total_endpoints': len(endpoint_results),
                'healthy_count': len([r for r in endpoint_results if r['status'] == 'healthy']),
                'unhealthy_count': len([r for r in endpoint_results if r['status'] != 'healthy']),
                'average_response_time': round(
                    sum(r['response_time'] for r in endpoint_results) / len(endpoint_results), 2
                ) if endpoint_results else 0
            }
        }
        
        logger.info(f"健康檢查完成 - 整體狀態: {overall_status}")
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """保存健康檢查報告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'health_report_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"報告已保存至: {filename}")
        return filename

def main():
    """主函數"""
    checker = HealthChecker()
    
    try:
        # 執行健康檢查
        report = checker.run_health_check()
        
        # 保存報告
        filename = checker.save_report(report)
        
        # 輸出摘要
        print("\n" + "="*50)
        print("健康檢查摘要")
        print("="*50)
        print(f"整體狀態: {report['overall_status']}")
        print(f"健康端點: {report['summary']['healthy_count']}/{report['summary']['total_endpoints']}")
        print(f"平均回應時間: {report['summary']['average_response_time']}ms")
        print(f"報告檔案: {filename}")
        
        # 如果有不健康的端點，顯示詳情
        unhealthy = [ep for ep in report['endpoints'] if ep['status'] != 'healthy']
        if unhealthy:
            print("\n不健康的端點:")
            for ep in unhealthy:
                print(f"  - {ep['name']}: {ep['status']} ({ep.get('error', 'N/A')})")
        
        print("="*50)
        
        # 根據整體狀態設置退出碼
        if report['overall_status'] == 'healthy':
            exit(0)
        elif report['overall_status'] == 'degraded':
            exit(1)
        else:
            exit(2)
            
    except Exception as e:
        logger.error(f"健康檢查執行失敗: {e}")
        exit(3)

if __name__ == '__main__':
    main()
