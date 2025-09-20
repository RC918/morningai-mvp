"""
監控儀表板 Web 介面
提供即時監控狀態查看和管理功能
"""

import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
from continuous_monitoring import ContinuousMonitor
import asyncio
import threading

app = Flask(__name__)

# 全域監控實例
monitor = None
monitor_thread = None

# HTML 模板
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MorningAI 監控儀表板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .status-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .status-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .status-card h3 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .status-card.healthy h3 {
            color: #27ae60;
        }
        
        .status-card.warning h3 {
            color: #f39c12;
        }
        
        .status-card.critical h3 {
            color: #e74c3c;
        }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
        }
        
        .service-card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .service-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .service-name {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .service-status {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-healthy {
            background: #d4edda;
            color: #155724;
        }
        
        .status-unhealthy {
            background: #f8d7da;
            color: #721c24;
        }
        
        .service-details {
            padding: 1.5rem;
        }
        
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }
        
        .detail-label {
            font-weight: 500;
            color: #666;
        }
        
        .detail-value {
            color: #333;
        }
        
        .url-link {
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
        }
        
        .url-link:hover {
            text-decoration: underline;
        }
        
        .error-message {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 0.75rem;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #856404;
        }
        
        .controls {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            margin: 0 0.5rem;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #5a6fd8;
        }
        
        .btn.danger {
            background: #e74c3c;
        }
        
        .btn.danger:hover {
            background: #c0392b;
        }
        
        .last-updated {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-top: 2rem;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .services-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 MorningAI 監控儀表板</h1>
        <p>即時監控系統狀態與服務健康度</p>
    </div>
    
    <div class="container">
        <div class="controls">
            <button class="btn" onclick="refreshData()">🔄 刷新數據</button>
            <button class="btn" onclick="toggleMonitoring()" id="toggleBtn">⏸️ 暫停監控</button>
            <button class="btn" onclick="exportData()">📊 匯出數據</button>
        </div>
        
        <div id="statusOverview" class="status-overview">
            <div class="loading">載入中...</div>
        </div>
        
        <div id="servicesGrid" class="services-grid">
            <div class="loading">載入服務狀態中...</div>
        </div>
        
        <div class="last-updated" id="lastUpdated">
            最後更新：載入中...
        </div>
    </div>
    
    <script>
        let monitoringActive = true;
        
        async function fetchData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('獲取數據失敗:', error);
            }
        }
        
        function updateDashboard(data) {
            updateStatusOverview(data);
            updateServicesGrid(data);
            updateLastUpdated();
        }
        
        function updateStatusOverview(data) {
            const overview = document.getElementById('statusOverview');
            const totalServices = data.total_services || 0;
            const healthyServices = data.healthy_services || 0;
            const failedServices = data.failed_services || 0;
            
            overview.innerHTML = `
                <div class="status-card healthy">
                    <h3>${healthyServices}</h3>
                    <p>正常服務</p>
                </div>
                <div class="status-card ${failedServices > 0 ? 'critical' : 'healthy'}">
                    <h3>${failedServices}</h3>
                    <p>異常服務</p>
                </div>
                <div class="status-card">
                    <h3>${totalServices}</h3>
                    <p>總服務數</p>
                </div>
                <div class="status-card ${data.monitoring_active ? 'healthy' : 'warning'}">
                    <h3>${data.monitoring_active ? '運行中' : '已停止'}</h3>
                    <p>監控狀態</p>
                </div>
            `;
        }
        
        function updateServicesGrid(data) {
            const grid = document.getElementById('servicesGrid');
            const services = data.services || [];
            
            if (services.length === 0) {
                grid.innerHTML = '<div class="loading">暫無服務數據</div>';
                return;
            }
            
            grid.innerHTML = services.map(service => `
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">${service.name}</div>
                        <div class="service-status ${service.is_healthy ? 'status-healthy' : 'status-unhealthy'}">
                            ${service.is_healthy ? '✅ 正常' : '❌ 異常'}
                        </div>
                    </div>
                    <div class="service-details">
                        <div class="detail-row">
                            <span class="detail-label">URL:</span>
                            <a href="${service.url}" target="_blank" class="detail-value url-link">${service.url}</a>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">狀態碼:</span>
                            <span class="detail-value">${service.status_code}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">回應時間:</span>
                            <span class="detail-value">${service.response_time ? service.response_time.toFixed(2) + 's' : 'N/A'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">最後檢查:</span>
                            <span class="detail-value">${service.last_check ? new Date(service.last_check).toLocaleString() : 'N/A'}</span>
                        </div>
                        ${service.error_message ? `
                            <div class="error-message">
                                <strong>錯誤訊息:</strong> ${service.error_message}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function updateLastUpdated() {
            const element = document.getElementById('lastUpdated');
            element.textContent = `最後更新：${new Date().toLocaleString()}`;
        }
        
        function refreshData() {
            fetchData();
        }
        
        async function toggleMonitoring() {
            try {
                const response = await fetch('/api/toggle-monitoring', { method: 'POST' });
                const data = await response.json();
                
                monitoringActive = data.monitoring_active;
                const btn = document.getElementById('toggleBtn');
                btn.textContent = monitoringActive ? '⏸️ 暫停監控' : '▶️ 開始監控';
                
                fetchData();
            } catch (error) {
                console.error('切換監控狀態失敗:', error);
            }
        }
        
        async function exportData() {
            try {
                const response = await fetch('/api/export');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `monitoring-data-${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('匯出數據失敗:', error);
            }
        }
        
        // 初始載入和自動刷新
        fetchData();
        setInterval(fetchData, 30000); // 每30秒刷新一次
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """監控儀表板首頁"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/api/status')
def get_status():
    """獲取監控狀態 API"""
    global monitor
    
    if not monitor:
        return jsonify({
            'error': '監控系統未初始化',
            'monitoring_active': False,
            'total_services': 0,
            'healthy_services': 0,
            'failed_services': 0,
            'services': []
        })
    
    try:
        # 獲取基本狀態
        status = monitor.get_monitoring_status()
        
        # 獲取最新的服務檢查結果
        services_data = []
        if monitor.results_history:
            # 按服務名稱分組，取最新結果
            latest_results = {}
            for result in reversed(monitor.results_history):
                if result.service_name not in latest_results:
                    latest_results[result.service_name] = result
            
            for service_name, result in latest_results.items():
                services_data.append({
                    'name': service_name,
                    'url': result.url,
                    'status_code': result.status_code,
                    'response_time': result.response_time,
                    'is_healthy': result.is_healthy,
                    'error_message': result.error_message,
                    'last_check': result.timestamp.isoformat()
                })
        
        return jsonify({
            **status,
            'services': services_data
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'monitoring_active': False,
            'total_services': 0,
            'healthy_services': 0,
            'failed_services': 0,
            'services': []
        })

@app.route('/api/toggle-monitoring', methods=['POST'])
def toggle_monitoring():
    """切換監控狀態"""
    global monitor, monitor_thread
    
    try:
        if monitor and monitor.monitoring_active:
            # 停止監控
            monitor.stop_monitoring()
            if monitor_thread:
                monitor_thread.join(timeout=5)
            
            return jsonify({
                'monitoring_active': False,
                'message': '監控已停止'
            })
        else:
            # 啟動監控
            if not monitor:
                monitor = ContinuousMonitor('/home/ubuntu/morningai-mvp/monitoring/monitoring_config.json')
            
            def run_monitor():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(monitor.start_monitoring())
            
            monitor_thread = threading.Thread(target=run_monitor, daemon=True)
            monitor_thread.start()
            
            return jsonify({
                'monitoring_active': True,
                'message': '監控已啟動'
            })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'monitoring_active': False
        }), 500

@app.route('/api/export')
def export_data():
    """匯出監控數據"""
    global monitor
    
    if not monitor:
        return jsonify({'error': '監控系統未初始化'}), 400
    
    try:
        export_data = {
            'export_time': datetime.utcnow().isoformat(),
            'monitoring_status': monitor.get_monitoring_status(),
            'services_config': monitor.services,
            'alert_config': monitor.alert_config.__dict__,
            'results_history': [
                {
                    'service_name': result.service_name,
                    'url': result.url,
                    'status_code': result.status_code,
                    'response_time': result.response_time,
                    'is_healthy': result.is_healthy,
                    'error_message': result.error_message,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in monitor.results_history[-100:]  # 最近100筆記錄
            ]
        }
        
        response = app.response_class(
            response=json.dumps(export_data, indent=2, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
        
        response.headers['Content-Disposition'] = f'attachment; filename=monitoring-export-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}.json'
        
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """儀表板健康檢查"""
    return jsonify({
        'status': 'ok',
        'service': 'monitoring-dashboard',
        'timestamp': datetime.utcnow().isoformat(),
        'monitoring_active': monitor.monitoring_active if monitor else False
    })

def init_monitor():
    """初始化監控系統"""
    global monitor, monitor_thread
    
    try:
        config_file = '/home/ubuntu/morningai-mvp/monitoring/monitoring_config.json'
        monitor = ContinuousMonitor(config_file)
        
        # 在背景執行緒中啟動監控
        def run_monitor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(monitor.start_monitoring())
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        print("✅ 監控系統已初始化並啟動")
    
    except Exception as e:
        print(f"❌ 監控系統初始化失敗：{e}")

if __name__ == '__main__':
    # 初始化監控系統
    init_monitor()
    
    # 啟動 Flask 應用
    port = int(os.environ.get('DASHBOARD_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
