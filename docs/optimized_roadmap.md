## MorningAI MVP 專案優化路線圖與建議

### 前言

本次優化路線圖基於先前成功解決 Vercel 部署問題的經驗，旨在提供一個更為穩健、高效且具備前瞻性的 MVP 開發路徑。我們將針對專案基礎建設、依賴管理、配置最佳化及部署流程等方面提出具體建議，以確保專案能順利推進並達成預期目標。

### 優化後的 MVP 分階段計劃

#### Phase 0｜專案基礎建設 (Project Infrastructure)

**目標：** 建立乾淨可維護的 monorepo，並確保開發環境的一致性。

**優化建議：**

*   **統一套件管理器：** 鑑於本次部署經驗，明確規定專案統一使用 `npm` 作為套件管理器。在專案初始化階段即移除 `pnpm-lock.yaml` 等其他套件管理器的鎖定檔案，並在 CI/CD 中強制檢查。
*   **基礎依賴項清單：** 在此階段就應列出所有核心依賴項（如 React, Vite, Tailwind CSS, PostCSS, `lucide-react`, `next-themes`, `sonner`, `@radix-ui/*` 等），並確保它們在 `apps/web/package.json` 中被正確聲明和安裝。
*   **PostCSS/Tailwind CSS 基礎配置：** 在此階段完成 `postcss.config.js` 和 `tailwind.config.js` 的初始配置，並進行一次最小化的本地構建測試，以驗證配置的正確性。
*   **CI/CD 增強：** 除了 Lint 和 Build 驗證，增加一個自動檢查 `package-lock.json` 與 `package.json` 一致性的步驟，防止因套件版本不一致導致的問題。

**交付物：** Commit SHA、/health OK、統一的 `package-lock.json`、基礎樣式構建成功。

#### Phase 1｜雲端可用 (Cloud Availability)

**目標：** 確保 API 和 Web 應用程式能在 Render 和 Vercel 上正常運作。

**優化建議：**

*   **Vercel 部署設定標準化：** 制定詳細的 Vercel 部署設定文件，明確指定 `Framework Preset` (Vite)、`Root Directory` (`apps/web`)、`Build Command` (`npm run build`)、`Install Command` (`npm install`) 和 `Output Directory` (`dist`)。這應作為標準操作流程的一部分。
*   **環境變數管理：** 強調環境變數的正確配置和安全性，例如 `VITE_API_BASE_URL` 和 `JWT_SECRET`，並建議使用 Vercel 和 Render 的環境變數管理功能。
*   **部署前檢查清單：** 在每次部署前，執行一個自動化腳本檢查所有必要的依賴項是否已安裝、配置文件是否正確、以及所有組件是否可解析。這有助於在部署到雲端之前捕獲錯誤。

**交付物：** Render API URL、Vercel Web URL、詳細的部署配置文檔。

#### Phase 2｜資料層與多租戶 (Data Layer & Multi-tenancy)

**目標：** 導入真實 DB 與多租戶基礎。

**優化建議：**

*   **數據庫連接測試：** 在部署後，增加自動化測試來驗證應用程式與 Postgres/Redis 的連接是否正常，並確保 `Alembic Migration` 能夠成功執行。
*   **多租戶架構設計文檔：** 提供詳細的多租戶架構設計文檔，包括數據庫 schema 設計、租戶隔離策略和 API 認證授權機制。

**交付物：** DB schema、/readiness 回傳、多租戶架構設計文檔。

#### Phase 3｜租戶 AI 功能 MVP (Tenant AI Feature MVP)

**目標：** 租戶能創建並測試 AI Bot。

**優化建議：**

*   **組件開發規範：** 針對新開發的組件（如 `StrategyManagement`, `DecisionApproval` 等），制定明確的開發規範，包括檔案命名、導入路徑、依賴項聲明等，以避免未來再次出現組件缺失或導入錯誤的問題。
*   **模組化設計：** 鼓勵將 AI 核心功能模組化，便於測試和迭代。例如，將 `Orchestrator Service` 和 `Demo Bot` 設計為可插拔的模組。
*   **國際化 (i18n) 測試：** 增加自動化測試來驗證 Web 應用程式的國際化功能 (zh-TW/en) 是否正常工作。

**交付物：** 租戶能在 Web 控制台啟用一個最小 AI Bot、新組件的開發規範。

#### Phase 4｜金流與點數系統 (Payment & Credit System)

**目標：** 租戶能註冊、充值、消耗點數。

**優化建議：**

*   **第三方服務集成測試：** 針對 Stripe/TapPay sandbox 串接，設計詳細的集成測試用例，確保金流和點數消耗流程的穩定性。
*   **安全審計：** 在此階段引入安全審計，特別是針對金流相關的 API 和數據處理，確保符合支付行業的安全標準。

**交付物：** 點數消耗流程測試成功、安全審計報告。

#### Phase 5｜AI 自主管理與 Bot Builder (AI Autonomous Management & Bot Builder)

**目標：** 提供 SaaS 級別的 AI 自治能力。

**優化建議：**

*   **可視化工具的技術選型：** 針對 `Bot Builder Console` 的可視化流程圖，提前進行技術選型和可行性研究，確保選用的技術棧能滿足需求並與現有專案兼容。
*   **任務追蹤與監控：** 規劃 `HITL Dashboard` 的數據來源和展示方式，確保能實時監控 AI 任務的狀態和性能。

**交付物：** 租戶能建立一個流程、Bot Builder 技術選型報告。

#### Phase 6｜正式上線與最佳化 (Go-Live & Optimization)

**目標：** 完整 SaaS MVP 上線。

**優化建議：**

*   **域名配置自動化：** 考慮使用腳本或自動化工具來配置 `www.morningai.me`、`app.morningai.me` 和 `api.morningai.me` 的域名，減少手動配置錯誤的風險。
*   **模板集成測試：** 對於官網和後台模板的套用，進行全面的集成測試，確保 UI/UX 的一致性和功能完整性。
*   **CORS 策略細化：** 在上線前，仔細審查並收斂 CORS 白名單，只允許必要的來源訪問，以增強安全性。
*   **日誌與監控系統：** 建立完善的結構化日誌、健康檢查和錯誤告警系統，確保在生產環境中能夠及時發現和解決問題。

**交付物：** 正式可用的 SaaS MVP、自動化部署腳本、監控報告。

### 總結

這份優化後的路線圖強調了在每個階段中，特別是在基礎建設和部署環節，需要更加細緻和嚴謹的規劃。通過統一工具、明確規範、增加自動化檢查和測試，我們能夠顯著降低未來開發和部署的風險，提高專案的穩定性和開發效率。這將有助於 MorningAI MVP 專案更快、更穩健地實現其商業目標。

