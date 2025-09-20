# MorningAI MVP (Monorepo)

這個倉庫託管 MorningAI MVP 的 monorepo 架構，是一個企業級 AI SaaS 多租戶平台。

## 🚀 快速開始

### 新開發者必讀文檔
- **[📋 專案全面概覽](docs/PROJECT_OVERVIEW.md)** - 了解專案願景、技術架構和當前進度
- **[🏗️ 技術架構文檔](docs/ARCHITECTURE.md)** - 深入了解系統設計和技術細節  
- **[👨‍💻 開發者快速上手指南](docs/DEVELOPER_GUIDE.md)** - 環境設置、開發流程和最佳實踐

### 專案結構
```
morningai-mvp/
├── apps/
│   ├── web/          # 前端應用 (Next.js/React + Tailwind CSS)
│   └── api/          # 後端 API (Python Flask + Supabase)
├── infra/            # 基礎設施配置 (Vercel/Render/Supabase/Terraform)
├── .github/workflows # CI/CD 管道 (GitHub Actions)
├── docs/             # 📚 完整專案文檔
├── scripts/          # 🔧 自動化腳本
├── supabase/         # 🗄️ 資料庫遷移和 RLS 政策
└── ops/env/          # 🔐 環境變數標準和腳本
```

## 🎯 專案願景

MorningAI MVP 是一個 **AI Agent 編排平台**，提供：
- **🤖 AI Agent 編排**: 通過 LangGraph DAG 實現複雜的 AI 工作流程
- **👥 HITL 控制台**: Human-in-the-Loop 智能決策介面
- **🏢 多租戶 SaaS**: 企業級多租戶架構
- **🔗 多通道整合**: 支援 LINE、Telegram、Slack、WhatsApp、WeChat
- **🔒 企業級安全**: 符合 GDPR、SOC2、ISO27001 標準

## 🛠️ 技術棧

### 前端
- **框架**: Next.js/React + TypeScript
- **UI**: Tailwind CSS + shadcn/ui + Tremor
- **部署**: Vercel

### 後端  
- **框架**: Python Flask + Flask-RESTX
- **資料庫**: Supabase (PostgreSQL + RLS)
- **快取**: Redis
- **部署**: Render (Docker)

### AI 編排
- **引擎**: LangGraph
- **Agent**: Content、Growth、Ad Buyer、CodeWriter、AutoQA

## ⚡ 快速設置

### 1. 環境準備
```bash
# Clone 專案
git clone https://github.com/RC918/morningai-mvp.git
cd morningai-mvp

# 複製環境變數模板
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local  
cp apps/api/.env.example apps/api/.env
```

### 2. 安裝依賴
```bash
# 根目錄依賴
npm install

# 前端依賴
cd apps/web && npm install && cd ../..

# 後端依賴  
cd apps/api && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cd ../..
```

### 3. 啟動開發環境
```bash
# 後端 API (終端 1)
cd apps/api && source venv/bin/activate && python src/main.py

# 前端應用 (終端 2)  
cd apps/web && npm run dev
```

### 4. 驗證環境
- 前端: http://localhost:3000
- 後端 API: http://localhost:5000/health
- API 文檔: http://localhost:5000/docs

## 📊 當前狀態

### ✅ 已完成 (Phase 0 - 基礎建設)
- Monorepo 架構和 CI/CD 管道
- 認證系統 (JWT + MFA + 帳戶鎖定)
- Row Level Security (RLS) 政策
- JWT 黑名單機制
- 代碼品質工具鏈
- API 文檔系統

### 🔄 進行中 (Phase 1 - MVP 上線)
- 多租戶註冊系統
- HITL 控制台開發
- 金流整合 (Stripe/TapPay)
- 監控與日誌系統

### 📋 計劃中 (Phase 2 - AI 編排層)
- LangGraph DAG 編排器
- 核心 AI Agent 實現
- Webhook → Agent → HITL 循環
- 多語系支援

## 🔒 安全特性

- **🔐 多層認證**: JWT + MFA + 帳戶鎖定
- **🛡️ 資料隔離**: RLS 政策 + 租戶隔離
- **🚫 Token 管理**: JWT 黑名單機制
- **📝 審計日誌**: 完整操作追蹤
- **⚡ 速率限制**: API 保護機制

## 📈 CI/CD 狀態

[![Env Check](https://github.com/RC918/morningai-mvp/actions/workflows/env-check.yml/badge.svg)](https://github.com/RC918/morningai-mvp/actions/workflows/env-check.yml)
[![Security Check](https://github.com/RC918/morningai-mvp/actions/workflows/security-check.yml/badge.svg)](https://github.com/RC918/morningai-mvp/actions/workflows/security-check.yml)

## 🌐 部署狀態

- **前端**: https://morningai-mvp-web.vercel.app ✅
- **後端**: https://morningai-mvp.onrender.com ✅  
- **健康檢查**: https://morningai-mvp.onrender.com/health ✅

## 📚 詳細文檔

### 核心文檔
- [📋 專案全面概覽](docs/PROJECT_OVERVIEW.md) - 業務願景、技術架構、路線圖
- [🏗️ 技術架構文檔](docs/ARCHITECTURE.md) - 系統設計、安全架構、擴展性
- [👨‍💻 開發者快速上手指南](docs/DEVELOPER_GUIDE.md) - 環境設置、開發流程、最佳實踐

### 技術文檔
- [🔒 RLS 政策文檔](docs/RLS_POLICIES.md) - 資料庫安全政策詳解
- [✨ 代碼品質指南](docs/CODE_QUALITY.md) - 代碼標準和工具使用
- [🚀 部署驗收報告](DEPLOYMENT_ACCEPTANCE_REPORT.md) - 部署狀態和驗收結果

### 運維文檔
- [🔧 代碼品質腳本](scripts/code-quality.sh) - 自動化品質檢查
- [📊 環境變數檢查清單](ENV_Handoff_Checklist.md) - 環境配置指南

## 🤝 貢獻指南

### 開發流程
1. **Fork 專案** 並創建功能分支
2. **遵循代碼規範** 和提交訊息格式
3. **運行測試** 確保所有檢查通過
4. **提交 Pull Request** 並等待代碼審查

### 代碼品質
```bash
# 運行完整品質檢查
./scripts/code-quality.sh

# 運行測試
npm test                    # 前端測試
pytest apps/api/tests/     # 後端測試
```

### 提交規範
```bash
feat: 新功能
fix: Bug 修復  
docs: 文檔更新
style: 代碼格式
refactor: 重構
test: 測試相關
chore: 構建或工具變動
```

## 📞 支援

- **🐛 Bug 報告**: [GitHub Issues](https://github.com/RC918/morningai-mvp/issues)
- **💡 功能建議**: [GitHub Discussions](https://github.com/RC918/morningai-mvp/discussions)  
- **📖 文檔問題**: 提交 PR 修正
- **❓ 技術問題**: 查看 [開發者指南](docs/DEVELOPER_GUIDE.md)

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案。

---

**🌅 MorningAI MVP** - 讓 AI 編排變得簡單而強大



<!-- chore: trigger CI -->



<!-- chore: trigger CI 2 -->
