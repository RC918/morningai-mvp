# CI/CD 設定指南

## 概述

本文件詳細說明 MorningAI MVP 專案的 CI/CD 工作流程設定和配置。

## 工作流程架構

### 主要工作流程檔案

- `.github/workflows/env-check.yml`: 環境檢查和測試工作流程

### 工作流程觸發條件

1. **Pull Request**: 當有 PR 提交到 main 分支時自動觸發
2. **手動觸發**: 透過 GitHub Actions 介面手動執行

## 環境變數驗證

### 驗證腳本

位置：`ops/env/scripts/check_env.mjs`

此腳本負責：
- 載入和驗證環境變數
- 檢查必要變數是否存在
- 驗證變數格式和長度

### 使用方式

```bash
node ops/env/scripts/check_env.mjs --env-file .env --app web
node ops/env/scripts/check_env.mjs --env-file .env --app api
```

### 支援的應用程式

- `web`: 前端應用程式
- `api`: 後端應用程式

## 矩陣策略配置

工作流程使用矩陣策略同時處理多個應用程式：

```yaml
strategy:
  matrix:
    app:
      - { name: web, path: apps/web }
      - { name: api, path: apps/api }
```

這允許並行執行前端和後端的測試。

## 測試階段

### 1. 環境設定

- 檢出程式碼
- 設定 Node.js 環境
- 安裝 dotenv 依賴

### 2. 環境變數建立

從 GitHub Secrets 建立 `.env` 檔案：

```yaml
- name: Create .env from GitHub Secrets
  run: |
    cat > ${{ matrix.app.path }}/.env << 'EOF'
    SUPABASE_URL=${{ secrets.SB_URL }}
    SUPABASE_ANON_KEY=${{ secrets.SB_ANON_KEY }}
    # ... 其他環境變數
    EOF
```

### 3. 前端測試 (web)

- 安裝 Node.js 依賴
- 執行環境變數檢查
- Lint 檢查
- Type 檢查
- 單元測試

### 4. 後端測試 (api)

- 設定 Python 環境
- 安裝 Python 依賴
- 執行環境變數檢查
- Lint 檢查 (flake8)
- Type 檢查 (mypy)
- 單元測試 (pytest)
- 健康檢查端點測試

## 證據收集

### 自動化報告

工作流程會自動在 PR 中發布測試結果評論：

```javascript
const commentBody = `
## 🔍 CI/CD 工作流程報告

**狀態**: ${jobStatus === 'success' ? '✅ 通過' : '❌ 失敗'}
**工作流程**: [Env Check](${jobUrl})
**時間**: ${new Date().toLocaleString()}
**應用程式**: ${{ matrix.app.name }}

### 測試結果:
- **環境檢查**: ${{ steps.run-env-check-for-web.outcome || steps.run-env-check-for-api.outcome || 'N/A' }}
- **Lint 檢查**: ${{ steps.web-lint-check.outcome || steps.api-lint-check.outcome || 'N/A' }}
- **Type 檢查**: ${{ steps.web-type-check.outcome || steps.api-type-check.outcome || 'N/A' }}
- **單元測試**: ${{ steps.web-unit-tests.outcome || steps.api-unit-tests.outcome || 'N/A' }}
- **健康檢查**: ${{ steps.api-health-check.outcome || 'N/A' }}
`;
```

### 報告內容

- 執行狀態 (成功/失敗)
- 工作流程連結
- 執行時間
- 各個測試階段的結果
- 詳細的摘要資訊

## GitHub Secrets 設定

### 必要的 Secrets

在 GitHub 儲存庫設定中需要配置以下 Secrets：

```
SB_URL=your_supabase_url
SB_ANON_KEY=your_supabase_anon_key
SB_SERVICE_ROLE_KEY=your_supabase_service_role_key
SB_JWT_SECRET=your_supabase_jwt_secret
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url
JWT_SECRET=your_jwt_secret
EMAIL_FROM=your_email_from
SMTP_HOST=your_smtp_host
SMTP_PORT=your_smtp_port
SMTP_USER=your_smtp_user
SMTP_PASS=your_smtp_pass
```

## 權限設定

工作流程需要以下權限：

```yaml
permissions:
  pull-requests: write
```

這允許工作流程在 PR 中發布評論。

## 故障排除

### 常見問題

1. **dotenv 模組找不到**
   - 解決方案：確保在 `ops/env/scripts` 目錄安裝 dotenv

2. **權限不足**
   - 解決方案：檢查 `permissions` 設定

3. **環境變數缺失**
   - 解決方案：檢查 GitHub Secrets 設定

4. **端口衝突**
   - 解決方案：使用不同的端口或終止衝突的進程

### 除錯技巧

1. 檢查工作流程日誌
2. 驗證環境變數設定
3. 本地測試腳本
4. 檢查依賴安裝

## 最佳實務

1. **安全性**
   - 不要在日誌中暴露敏感資訊
   - 使用 GitHub Secrets 管理敏感資料

2. **效能**
   - 使用矩陣策略並行執行測試
   - 快取依賴以加速建置

3. **可維護性**
   - 保持工作流程檔案簡潔
   - 使用描述性的步驟名稱
   - 定期更新依賴版本

4. **監控**
   - 設定失敗通知
   - 定期檢查工作流程效能
   - 監控測試覆蓋率

