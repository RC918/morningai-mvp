# MorningAI-MVP 運維操作手冊

## 專案概覽

**專案名稱**: MorningAI-MVP  
**架構**: 前後端分離 (React + Flask)  
**部署平台**: Vercel (前端) + Render (後端)  
**資料庫**: Supabase PostgreSQL  
**監控**: 內建健康檢查端點  

## 部署架構

### 前端應用 (Web)
- **平台**: Vercel
- **專案 ID**: prj_sDB39CsQV8ay3gdTOiDGH4vcfLEI
- **部署 URL**: https://morningai-mvp-web.vercel.app
- **構建命令**: `npm run build`
- **輸出目錄**: `dist/`

### 後端應用 (API)
- **平台**: Render
- **服務 ID**: srv_xxx (需要從 Render 控制台獲取)
- **部署 URL**: https://morningai-mvp.onrender.com
- **健康檢查**: `/health`
- **啟動命令**: `gunicorn src.main:app`

## 環境變數配置

### 前端環境變數 (Vercel)
```bash
VITE_API_BASE_URL=https://morningai-mvp.onrender.com
VITE_SB_URL=https://xxx.supabase.co
VITE_SB_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_APP_ENV=production
```

### 後端環境變數 (Render)
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
JWT_SECRET=your-jwt-secret-key
SB_URL=https://xxx.supabase.co
SB_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SB_JWT_SECRET=your-supabase-jwt-secret
EMAIL_FROM=noreply@morningai.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

## 監控與健康檢查

### 健康檢查端點
- **URL**: `https://morningai-mvp.onrender.com/health`
- **預期回應**:
  ```json
  {
    "status": "ok",
    "timestamp": "2025-09-21T13:45:30Z",
    "version": "1.0.0"
  }
  ```

### Render 內建監控
- **Health Check Path**: `/health`
- **檢查間隔**: 每 30 秒
- **超時時間**: 10 秒
- **失敗閾值**: 連續 3 次失敗觸發重啟

### 外部監控 (可選)
如需設置外部 uptime 監控服務 (如 UptimeRobot)，請監控以下端點：
- 前端: https://morningai-mvp-web.vercel.app
- 後端: https://morningai-mvp.onrender.com/health

## CI/CD 工作流程

### 主要工作流程
1. **CI Check** (`.github/workflows/ci-check.yml`)
   - 代碼風格檢查 (ESLint, Black, isort)
   - 類型檢查 (TypeScript, mypy)
   - 單元測試 (Jest, pytest)
   - 健康檢查驗證

2. **環境檢查** (`.github/workflows/env-check.yml`)
   - 環境變數完整性檢查
   - 導入煙霧測試
   - 部署前驗證

3. **Release** (`.github/workflows/release.yml`)
   - 構建 Docker 映像檔
   - 打包前端資源
   - 準備遷移腳本
   - 自動部署到生產環境
   - 生成部署證明文檔

### 手動觸發部署
```bash
# 觸發 release workflow
gh workflow run release.yml -f tag=v1.0.0 -f is_hotfix=false

# 檢查工作流程狀態
gh run list --workflow=release.yml --limit=5
```

## 資料庫管理

### Supabase 連接
- **專案 URL**: https://xxx.supabase.co
- **資料庫**: PostgreSQL 15
- **連接池**: pgBouncer
- **備份**: 自動每日備份

### 遷移管理
```bash
# 檢查遷移狀態
cd apps/api
alembic current

# 執行遷移
alembic upgrade head

# 創建新遷移
alembic revision --autogenerate -m "描述"
```

### RLS (Row Level Security) 政策
- 已啟用租戶隔離
- 測試腳本: `scripts/rls_security_test.py`
- 測試報告: `rls_security_test_report.json`

## 故障排除

### 常見問題

#### 1. 健康檢查失敗
```bash
# 檢查服務狀態
curl -I https://morningai-mvp.onrender.com/health

# 檢查日誌
# 在 Render 控制台查看 "Logs" 標籤
```

#### 2. 環境變數問題
```bash
# 驗證環境變數
cd ops/env/scripts
node check_env.mjs
```

#### 3. 資料庫連接問題
```bash
# 測試資料庫連接
cd apps/api
python -c "from src.database import db; print('DB connection OK')"
```

#### 4. JWT 黑名單問題
```bash
# 檢查 JWT 黑名單功能
cd apps/api
pytest src/tests/test_jwt_blacklist.py -v
```

### 緊急聯絡資訊
- **技術負責人**: [待填入]
- **Render 支援**: https://render.com/support
- **Vercel 支援**: https://vercel.com/support
- **Supabase 支援**: https://supabase.com/support

## 安全注意事項

### 敏感資訊管理
- 所有 API 金鑰和密碼存儲在各平台的環境變數中
- JWT 密鑰定期輪換 (建議每 90 天)
- 資料庫憑證使用 Supabase 管理

### 存取控制
- GitHub 倉庫設有分支保護規則
- 生產環境部署需要 PR 審核
- 敏感操作需要雙重認證

### 安全監控
- 定期運行 `pip-audit` 檢查 Python 依賴漏洞
- 定期運行 `npm audit` 檢查 Node.js 依賴漏洞
- 監控異常登入和 API 調用模式

## 效能優化

### 前端優化
- 使用 Vite 進行快速構建
- 啟用 gzip 壓縮
- CDN 快取靜態資源

### 後端優化
- 使用 gunicorn 多進程部署
- 啟用 Redis 快取 (可選)
- 資料庫查詢優化

### 監控指標
- 回應時間 < 500ms (P95)
- 可用性 > 99.9%
- 錯誤率 < 0.1%

---

**最後更新**: 2025-09-21  
**文檔版本**: 1.0  
**維護者**: MorningAI 開發團隊
