# MorningAI MVP 部署指南

## 概述

本文件說明如何部署 MorningAI MVP monorepo 專案，包含前端和後端應用程式的部署步驟。

## 專案結構

```
morningai-mvp-monorepo/
├── apps/
│   ├── web/          # 前端應用程式 (React + Vite)
│   └── api/          # 後端應用程式 (Flask)
├── ops/
│   └── env/
│       └── scripts/  # 環境變數驗證腳本
└── .github/
    └── workflows/    # CI/CD 工作流程
```

## 環境變數配置

### 前端應用程式 (apps/web)

前端應用程式需要以下環境變數：

- `SUPABASE_URL`: Supabase 專案 URL
- `SUPABASE_ANON_KEY`: Supabase 匿名金鑰

### 後端應用程式 (apps/api)

後端應用程式需要以下環境變數：

- `SUPABASE_URL`: Supabase 專案 URL
- `SUPABASE_ANON_KEY`: Supabase 匿名金鑰
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase 服務角色金鑰
- `SUPABASE_JWT_SECRET`: Supabase JWT 密鑰
- `DATABASE_URL`: 資料庫連接字串
- `REDIS_URL`: Redis 連接字串
- `JWT_SECRET`: JWT 簽名密鑰
- `EMAIL_FROM`: 發送郵件地址
- `SMTP_HOST`: SMTP 伺服器主機
- `SMTP_PORT`: SMTP 伺服器端口
- `SMTP_USER`: SMTP 使用者名稱
- `SMTP_PASS`: SMTP 密碼

## 本地開發

### 前端開發

```bash
cd apps/web
npm install
npm run dev
```

前端應用程式將在 http://localhost:5173 運行。

### 後端開發

```bash
cd apps/api
pip install -r requirements.txt
python src/main.py
```

後端應用程式將在 http://localhost:5000 運行。

健康檢查端點：http://localhost:5000/health

## CI/CD 工作流程

專案使用 GitHub Actions 進行自動化測試和部署：

### 環境檢查工作流程 (.github/workflows/env-check.yml)

此工作流程執行以下檢查：

1. **環境變數驗證**: 使用 `ops/env/scripts/check_env.mjs` 驗證環境變數
2. **Lint 檢查**: 檢查程式碼品質
3. **Type 檢查**: 檢查型別正確性
4. **單元測試**: 執行單元測試
5. **健康檢查**: 測試後端健康檢查端點

### 觸發條件

- Pull Request 到 main 分支
- 手動觸發 (workflow_dispatch)

### 矩陣策略

工作流程使用矩陣策略同時測試前端和後端：

```yaml
strategy:
  matrix:
    app:
      - { name: web, path: apps/web }
      - { name: api, path: apps/api }
```

## 部署步驟

### 1. 環境準備

確保所有必要的環境變數已在 GitHub Secrets 中設定：

- `SB_URL`
- `SB_ANON_KEY`
- `SB_SERVICE_ROLE_KEY`
- `SB_JWT_SECRET`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `EMAIL_FROM`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`

### 2. 前端部署

前端應用程式可以部署到 Vercel、Netlify 或其他靜態網站託管服務。

### 3. 後端部署

後端應用程式可以部署到 Render、Heroku 或其他 Python 託管服務。

確保部署環境中設定了所有必要的環境變數。

## 故障排除

### 常見問題

1. **dotenv 模組找不到**: 確保在正確的目錄安裝 dotenv 依賴
2. **端口衝突**: 如果端口 5000 被佔用，可以使用其他端口
3. **環境變數缺失**: 檢查 .env 檔案或環境變數設定

### 日誌檢查

- 前端日誌: `apps/web/web_dev.log`
- 後端日誌: `apps/api/api_dev.log`

## 安全考量

1. 不要將敏感資訊提交到版本控制系統
2. 使用強密碼和安全的 JWT 密鑰
3. 定期更新依賴套件
4. 在生產環境中禁用除錯模式

## 監控和維護

1. 定期檢查健康檢查端點
2. 監控應用程式效能和錯誤日誌
3. 保持依賴套件更新
4. 定期備份資料庫

