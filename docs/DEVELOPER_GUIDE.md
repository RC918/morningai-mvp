# MorningAI MVP 開發者快速上手指南

## 🚀 快速開始

本指南幫助新開發者快速上手 MorningAI MVP 專案，包括環境設置、開發流程和常見問題解決。

---

## 📋 前置需求

### 必要工具
- **Node.js**: v18+ (推薦使用 nvm 管理版本)
- **Python**: 3.11+ (推薦使用 pyenv 管理版本)
- **Git**: 最新版本
- **Docker**: 用於本地開發環境 (可選)
- **VS Code**: 推薦的 IDE (含推薦擴展)

### 推薦的 VS Code 擴展
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml"
  ]
}
```

---

## 🛠️ 環境設置

### 1. Clone 專案
```bash
git clone https://github.com/RC918/morningai-mvp.git
cd morningai-mvp
```

### 2. 設置環境變數

#### 複製環境變數模板
```bash
# 根目錄環境變數
cp .env.example .env

# 前端環境變數
cp apps/web/.env.example apps/web/.env.local

# 後端環境變數
cp apps/api/.env.example apps/api/.env
```

#### 填入必要的環境變數
```bash
# .env (根目錄)
SB_URL=your_supabase_url
SB_ANON_KEY=your_supabase_anon_key
SB_SERVICE_ROLE_KEY=your_supabase_service_role_key
SB_JWT_SECRET=your_supabase_jwt_secret
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url
JWT_SECRET=your_jwt_secret

# apps/web/.env.local
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:5000

# apps/api/.env
DATABASE_URL=your_database_url
SB_SERVICE_ROLE_KEY=your_supabase_service_role_key
SB_JWT_SECRET=your_supabase_jwt_secret
JWT_SECRET=your_jwt_secret
REDIS_URL=redis://localhost:6379
```

### 3. 安裝依賴

#### 根目錄依賴 (Monorepo 管理)
```bash
npm install
```

#### 前端依賴
```bash
cd apps/web
npm install
cd ../..
```

#### 後端依賴
```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 開發依賴
cd ../..
```

### 4. 資料庫設置

#### 運行資料庫遷移
```bash
cd apps/api
source venv/bin/activate
alembic upgrade head
cd ../..
```

#### 應用 RLS 政策 (如果使用 Supabase)
```bash
# 在 Supabase SQL Editor 中執行
psql -f supabase/migrations/20250919_create_rls_policies.sql
```

---

## 🏃‍♂️ 本地開發

### 啟動開發服務

#### 方法 1: 分別啟動 (推薦)
```bash
# 終端 1: 啟動後端 API
cd apps/api
source venv/bin/activate
python src/main.py

# 終端 2: 啟動前端
cd apps/web
npm run dev

# 終端 3: 啟動 Redis (如果本地沒有)
redis-server
```

#### 方法 2: 使用 Docker Compose
```bash
# 啟動完整本地環境
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

### 驗證環境
```bash
# 檢查後端健康狀態
curl http://localhost:5000/health

# 檢查前端
open http://localhost:3000

# 檢查 API 文檔
open http://localhost:5000/docs
```

---

## 🔧 開發工具和腳本

### 代碼品質檢查
```bash
# 運行完整的代碼品質檢查
./scripts/code-quality.sh

# 分別運行各項檢查
./scripts/code-quality.sh --lint-only
./scripts/code-quality.sh --format-only
./scripts/code-quality.sh --test-only
```

### 前端開發工具
```bash
cd apps/web

# 開發服務器
npm run dev

# 類型檢查
npm run type-check

# Linting
npm run lint
npm run lint:fix

# 格式化
npm run format

# 測試
npm test
npm run test:watch
npm run test:coverage

# 構建
npm run build
```

### 後端開發工具
```bash
cd apps/api
source venv/bin/activate

# 開發服務器 (with auto-reload)
python src/main.py

# 代碼格式化
black src/
isort src/

# Linting
flake8 src/
bandit -r src/

# 類型檢查
mypy src/

# 測試
pytest
pytest --cov=src
pytest --cov=src --cov-report=html

# 資料庫遷移
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

---

## 📁 專案結構詳解

### 前端結構 (`apps/web/`)
```
apps/web/
├── src/
│   ├── components/          # 可重用組件
│   │   ├── ui/             # shadcn/ui 基礎組件
│   │   ├── forms/          # 表單組件
│   │   └── layout/         # 布局組件
│   ├── pages/              # 頁面組件
│   │   ├── auth/           # 認證相關頁面
│   │   ├── dashboard/      # 儀表板頁面
│   │   └── settings/       # 設置頁面
│   ├── hooks/              # 自定義 React Hooks
│   ├── utils/              # 工具函數
│   ├── types/              # TypeScript 類型定義
│   ├── styles/             # 全域樣式
│   └── lib/                # 第三方庫配置
├── public/                 # 靜態資源
├── tests/                  # 測試檔案
└── docs/                   # 前端文檔
```

### 後端結構 (`apps/api/`)
```
apps/api/
├── src/
│   ├── models/             # 資料模型
│   │   ├── user.py
│   │   ├── tenant.py
│   │   └── agent_task.py
│   ├── routes/             # API 路由
│   │   ├── auth.py
│   │   ├── admin.py
│   │   └── agents.py
│   ├── services/           # 業務邏輯服務
│   │   ├── auth_service.py
│   │   ├── tenant_service.py
│   │   └── agent_service.py
│   ├── utils/              # 工具函數
│   ├── decorators.py       # 裝飾器
│   ├── database.py         # 資料庫配置
│   └── main.py             # 應用入口點
├── tests/                  # 測試檔案
├── migrations/             # 資料庫遷移
├── scripts/                # 腳本檔案
└── docs/                   # 後端文檔
```

---

## 🧪 測試策略

### 前端測試

#### 單元測試 (Jest + React Testing Library)
```typescript
// src/components/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

#### 整合測試 (Cypress)
```typescript
// cypress/e2e/auth.cy.ts
describe('Authentication', () => {
  it('should login successfully', () => {
    cy.visit('/login')
    cy.get('[data-testid=email]').type('test@example.com')
    cy.get('[data-testid=password]').type('password123')
    cy.get('[data-testid=submit]').click()
    cy.url().should('include', '/dashboard')
  })
})
```

### 後端測試

#### 單元測試 (Pytest)
```python
# tests/test_auth_service.py
import pytest
from src.services.auth_service import AuthService

class TestAuthService:
    def test_authenticate_valid_credentials(self):
        auth_service = AuthService()
        result = auth_service.authenticate('test@example.com', 'password123')
        assert result.success is True
        assert result.token is not None

    def test_authenticate_invalid_credentials(self):
        auth_service = AuthService()
        result = auth_service.authenticate('test@example.com', 'wrong_password')
        assert result.success is False
        assert result.token is None
```

#### API 測試 (Pytest + FastAPI TestClient)
```python
# tests/test_auth_routes.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_login_endpoint():
    response = client.post('/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json()
```

---

## 🔄 開發流程

### Git 工作流程

#### 分支策略
```bash
# 主要分支
main                    # 生產環境分支
develop                 # 開發環境分支 (可選)

# 功能分支
feature/user-auth       # 新功能開發
feature/agent-service   # 新功能開發

# 修復分支
hotfix/security-patch   # 緊急修復
bugfix/login-issue      # 一般 Bug 修復
```

#### 開發流程
```bash
# 1. 創建功能分支
git checkout main
git pull origin main
git checkout -b feature/new-feature

# 2. 開發和提交
git add .
git commit -m "feat: add new feature"

# 3. 推送分支
git push origin feature/new-feature

# 4. 創建 Pull Request
# 在 GitHub 上創建 PR

# 5. 代碼審查和合併
# 通過 PR 審查後合併到 main
```

### 提交訊息規範 (Conventional Commits)
```bash
# 格式: <type>(<scope>): <description>

# 類型
feat:     # 新功能
fix:      # Bug 修復
docs:     # 文檔更新
style:    # 代碼格式 (不影響功能)
refactor: # 重構 (不是新功能也不是修復)
test:     # 測試相關
chore:    # 構建過程或輔助工具的變動

# 範例
feat(auth): add JWT token refresh mechanism
fix(api): resolve CORS issue in production
docs(readme): update installation instructions
```

### Pull Request 檢查清單
- [ ] 代碼通過所有 linting 檢查
- [ ] 所有測試通過
- [ ] 新功能有對應的測試
- [ ] 文檔已更新 (如果需要)
- [ ] 環境變數已更新 (如果需要)
- [ ] 資料庫遷移已創建 (如果需要)
- [ ] 安全性考量已評估
- [ ] 性能影響已評估

---

## 🐛 常見問題和解決方案

### 環境問題

#### 問題: Node.js 版本不相容
```bash
# 解決方案: 使用 nvm 管理 Node.js 版本
nvm install 18
nvm use 18
```

#### 問題: Python 虛擬環境問題
```bash
# 解決方案: 重新創建虛擬環境
cd apps/api
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 問題: 資料庫連接失敗
```bash
# 檢查環境變數
echo $DATABASE_URL

# 檢查資料庫服務狀態
pg_isready -h localhost -p 5432

# 檢查 Supabase 連接
curl -H "apikey: $SB_ANON_KEY" "$SB_URL/rest/v1/"
```

### 開發問題

#### 問題: 前端熱重載不工作
```bash
# 解決方案: 檢查 Vite 配置
# vite.config.js
export default {
  server: {
    watch: {
      usePolling: true
    }
  }
}
```

#### 問題: API CORS 錯誤
```python
# 解決方案: 檢查 CORS 配置
# src/main.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])
```

#### 問題: JWT Token 過期
```bash
# 檢查 Token 有效期
# 實施 Token 刷新機制
# 檢查系統時間同步
```

### 部署問題

#### 問題: Vercel 部署失敗
```bash
# 檢查構建日誌
vercel logs

# 檢查環境變數
vercel env ls

# 本地測試構建
npm run build
```

#### 問題: Render 服務啟動失敗
```bash
# 檢查 Dockerfile
docker build -t test-image .
docker run test-image

# 檢查環境變數
# 檢查健康檢查端點
```

---

## 📚 學習資源

### 技術文檔
- [Next.js 文檔](https://nextjs.org/docs)
- [Flask 文檔](https://flask.palletsprojects.com/)
- [Supabase 文檔](https://supabase.com/docs)
- [Tailwind CSS 文檔](https://tailwindcss.com/docs)
- [shadcn/ui 文檔](https://ui.shadcn.com/)

### 專案相關文檔
- [`PROJECT_OVERVIEW.md`](./PROJECT_OVERVIEW.md) - 專案全面概覽
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - 技術架構詳解
- [`RLS_POLICIES.md`](./RLS_POLICIES.md) - 資料庫安全政策
- [`CODE_QUALITY.md`](./CODE_QUALITY.md) - 代碼品質指南

### 最佳實踐
- [React 最佳實踐](https://react.dev/learn)
- [Python 最佳實踐](https://docs.python-guide.org/)
- [API 設計最佳實踐](https://restfulapi.net/)
- [安全最佳實踐](https://owasp.org/www-project-top-ten/)

---

## 🤝 團隊協作

### 溝通渠道
- **技術討論**: GitHub Issues 和 Discussions
- **代碼審查**: GitHub Pull Request Review
- **日常溝通**: Slack/Discord
- **文檔協作**: Notion + GitHub Wiki

### 開發規範
- **代碼風格**: 遵循 ESLint 和 Flake8 規則
- **命名規範**: 使用有意義的變數和函數名稱
- **註釋規範**: 複雜邏輯必須有註釋說明
- **測試規範**: 新功能必須有對應測試

### 求助指南
1. **查看文檔**: 先查看相關技術文檔
2. **搜尋 Issues**: 檢查是否有類似問題
3. **本地調試**: 使用調試工具排查問題
4. **提問格式**: 提供完整的錯誤信息和重現步驟
5. **團隊討論**: 在適當的渠道尋求幫助

---

## 🎯 下一步

### 新手任務建議
1. **熟悉代碼庫**: 閱讀主要組件和 API
2. **運行測試**: 確保本地環境正常
3. **小功能開發**: 從簡單的 UI 組件開始
4. **Bug 修復**: 處理一些簡單的 Bug
5. **文檔貢獻**: 改進文檔和註釋

### 進階任務
1. **新功能開發**: 實現完整的功能模組
2. **性能優化**: 改進應用性能
3. **安全增強**: 實施安全最佳實踐
4. **架構改進**: 參與架構設計討論
5. **導師角色**: 幫助其他新開發者

---

**文檔維護者**: Manus AI  
**最後更新**: 2025-09-20  
**版本**: v1.0

如有任何問題，請在 GitHub Issues 中提出或聯絡團隊成員。
