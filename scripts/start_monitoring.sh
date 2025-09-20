#!/bin/bash

# MorningAI MVP 監控系統啟動腳本
# 用於啟動持續監控和儀表板服務

set -e

echo "🚀 啟動 MorningAI MVP 監控系統..."

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝"
    exit 1
fi

# 檢查必要的 Python 套件
echo "📦 檢查 Python 依賴..."
python3 -c "import aiohttp, requests, flask" 2>/dev/null || {
    echo "📥 安裝必要的 Python 套件..."
    pip3 install aiohttp requests flask
}

# 設定工作目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_DIR/monitoring"

cd "$MONITORING_DIR"

# 檢查配置檔案
if [ ! -f "monitoring_config.json" ]; then
    echo "❌ 監控配置檔案不存在：monitoring_config.json"
    exit 1
fi

echo "✅ 配置檔案檢查完成"

# 設定環境變數
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# 設定日誌目錄
LOG_DIR="/tmp/morningai-monitoring"
mkdir -p "$LOG_DIR"

# 啟動監控服務的函數
start_monitoring() {
    echo "🔍 啟動持續監控服務..."
    
    # 檢查是否已有監控程序在運行
    if pgrep -f "continuous_monitoring.py" > /dev/null; then
        echo "⚠️  監控程序已在運行中"
        return 0
    fi
    
    # 在背景啟動監控
    nohup python3 continuous_monitoring.py > "$LOG_DIR/monitoring.log" 2>&1 &
    MONITOR_PID=$!
    
    echo "✅ 監控服務已啟動 (PID: $MONITOR_PID)"
    echo "$MONITOR_PID" > "$LOG_DIR/monitor.pid"
}

# 啟動儀表板的函數
start_dashboard() {
    echo "📊 啟動監控儀表板..."
    
    # 檢查是否已有儀表板在運行
    if pgrep -f "dashboard.py" > /dev/null; then
        echo "⚠️  儀表板已在運行中"
        return 0
    fi
    
    # 設定儀表板端口
    export DASHBOARD_PORT=${DASHBOARD_PORT:-8080}
    
    # 在背景啟動儀表板
    nohup python3 dashboard.py > "$LOG_DIR/dashboard.log" 2>&1 &
    DASHBOARD_PID=$!
    
    echo "✅ 監控儀表板已啟動 (PID: $DASHBOARD_PID, Port: $DASHBOARD_PORT)"
    echo "$DASHBOARD_PID" > "$LOG_DIR/dashboard.pid"
}

# 停止服務的函數
stop_services() {
    echo "🛑 停止監控服務..."
    
    # 停止監控程序
    if [ -f "$LOG_DIR/monitor.pid" ]; then
        MONITOR_PID=$(cat "$LOG_DIR/monitor.pid")
        if kill -0 "$MONITOR_PID" 2>/dev/null; then
            kill "$MONITOR_PID"
            echo "✅ 監控服務已停止"
        fi
        rm -f "$LOG_DIR/monitor.pid"
    fi
    
    # 停止儀表板
    if [ -f "$LOG_DIR/dashboard.pid" ]; then
        DASHBOARD_PID=$(cat "$LOG_DIR/dashboard.pid")
        if kill -0 "$DASHBOARD_PID" 2>/dev/null; then
            kill "$DASHBOARD_PID"
            echo "✅ 儀表板已停止"
        fi
        rm -f "$LOG_DIR/dashboard.pid"
    fi
    
    # 清理其他相關程序
    pkill -f "continuous_monitoring.py" 2>/dev/null || true
    pkill -f "dashboard.py" 2>/dev/null || true
}

# 檢查服務狀態
check_status() {
    echo "📋 檢查監控服務狀態..."
    
    # 檢查監控程序
    if pgrep -f "continuous_monitoring.py" > /dev/null; then
        MONITOR_PID=$(pgrep -f "continuous_monitoring.py")
        echo "✅ 監控服務運行中 (PID: $MONITOR_PID)"
    else
        echo "❌ 監控服務未運行"
    fi
    
    # 檢查儀表板
    if pgrep -f "dashboard.py" > /dev/null; then
        DASHBOARD_PID=$(pgrep -f "dashboard.py")
        DASHBOARD_PORT=${DASHBOARD_PORT:-8080}
        echo "✅ 儀表板運行中 (PID: $DASHBOARD_PID, Port: $DASHBOARD_PORT)"
        echo "🌐 儀表板訪問地址: http://localhost:$DASHBOARD_PORT"
    else
        echo "❌ 儀表板未運行"
    fi
    
    # 檢查日誌檔案
    if [ -f "$LOG_DIR/monitoring.log" ]; then
        echo "📄 監控日誌: $LOG_DIR/monitoring.log"
        echo "   最新日誌:"
        tail -3 "$LOG_DIR/monitoring.log" | sed 's/^/   /'
    fi
    
    if [ -f "$LOG_DIR/dashboard.log" ]; then
        echo "📄 儀表板日誌: $LOG_DIR/dashboard.log"
    fi
}

# 測試監控功能
test_monitoring() {
    echo "🧪 測試監控功能..."
    
    # 測試健康檢查
    echo "測試後端健康檢查..."
    if curl -s -f "https://morningai-mvp.onrender.com/health" > /dev/null; then
        echo "✅ 後端健康檢查正常"
    else
        echo "❌ 後端健康檢查失敗"
    fi
    
    # 測試前端
    echo "測試前端應用..."
    if curl -s -f "https://morningai-mvp-web.vercel.app" > /dev/null; then
        echo "✅ 前端應用正常"
    else
        echo "❌ 前端應用異常"
    fi
    
    # 測試 API 文檔
    echo "測試 API 文檔..."
    if curl -s -f "https://morningai-mvp.onrender.com/docs/" > /dev/null; then
        echo "✅ API 文檔正常"
    else
        echo "❌ API 文檔異常"
    fi
}

# 主要邏輯
case "${1:-start}" in
    "start")
        echo "🚀 啟動監控系統..."
        start_monitoring
        start_dashboard
        sleep 2
        check_status
        echo ""
        echo "🎉 監控系統啟動完成！"
        echo "📊 儀表板地址: http://localhost:${DASHBOARD_PORT:-8080}"
        echo "📄 日誌目錄: $LOG_DIR"
        ;;
    
    "stop")
        stop_services
        echo "🎉 監控系統已停止"
        ;;
    
    "restart")
        echo "🔄 重啟監控系統..."
        stop_services
        sleep 2
        start_monitoring
        start_dashboard
        sleep 2
        check_status
        echo "🎉 監控系統重啟完成！"
        ;;
    
    "status")
        check_status
        ;;
    
    "test")
        test_monitoring
        ;;
    
    "logs")
        echo "📄 監控日誌 (最新 20 行):"
        if [ -f "$LOG_DIR/monitoring.log" ]; then
            tail -20 "$LOG_DIR/monitoring.log"
        else
            echo "日誌檔案不存在"
        fi
        ;;
    
    "dashboard-logs")
        echo "📄 儀表板日誌 (最新 20 行):"
        if [ -f "$LOG_DIR/dashboard.log" ]; then
            tail -20 "$LOG_DIR/dashboard.log"
        else
            echo "日誌檔案不存在"
        fi
        ;;
    
    *)
        echo "使用方法: $0 {start|stop|restart|status|test|logs|dashboard-logs}"
        echo ""
        echo "指令說明:"
        echo "  start           - 啟動監控系統和儀表板"
        echo "  stop            - 停止所有監控服務"
        echo "  restart         - 重啟監控系統"
        echo "  status          - 檢查服務運行狀態"
        echo "  test            - 測試監控目標的可用性"
        echo "  logs            - 查看監控日誌"
        echo "  dashboard-logs  - 查看儀表板日誌"
        echo ""
        echo "環境變數:"
        echo "  DASHBOARD_PORT  - 儀表板端口 (預設: 8080)"
        exit 1
        ;;
esac
