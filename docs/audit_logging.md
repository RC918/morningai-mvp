# 審計日誌 (Audit Logging) 實作摘要

## 1. 概述

本文件概述了 MorningAI MVP 專案中審計日誌功能的實作細節。審計日誌是記錄系統中所有重要事件和活動的機制，對於安全監控、合規性要求、故障排除和用戶行為分析至關重要。

## 2. 實作方法

審計日誌的實作主要透過在 Flask 應用程式中定義 `AuditLog` 模型，並在關鍵操作中記錄審計事件。具體步驟如下：

### 2.1. 資料模型定義 (`models.py`)

*   **`AuditLog` 模型**：在 `models.py` 中定義了 `AuditLog` 模型，用於儲存審計事件。該模型包含以下欄位：
    *   `id`: 審計日誌的唯一識別碼。
    *   `user_id`: 執行操作的用戶 ID，與 `User` 模型建立外鍵關聯。
    *   `action`: 執行的操作類型（例如 "User Registration", "User Login", "Access Admin Page"）。
    *   `details`: 操作的詳細描述。
    *   `timestamp`: 操作發生的時間戳。

### 2.2. 審計日誌函數 (`auth.py`)

*   **`log_audit_event` 函數**：在 `auth.py` 中新增 `log_audit_event(user_id, action, details)` 函數。此函數負責將審計事件寫入 `AuditLog` 資料表。它會接收用戶 ID、操作類型和詳細描述作為參數，並創建一個新的 `AuditLog` 實例並儲存到資料庫中。

### 2.3. Flask 應用程式整合 (`main.py`)

*   **事件記錄**：在 `main.py` 的關鍵路由中（例如 `/register`, `/login`, `/logout`, `/admin-only`）呼叫 `log_audit_event` 函數，以記錄相應的用戶活動。這確保了用戶註冊、登入、登出以及存取受保護資源等重要操作都被記錄下來。

## 3. 測試

審計日誌功能的測試是中期改進測試的一部分，確保了審計事件的正確記錄。測試涵蓋了以下場景：

*   用戶註冊時，成功記錄 "User Registration" 事件。
*   用戶登入時，成功記錄 "User Login" 事件。
*   管理員用戶存取管理員頁面時，成功記錄 "Access Admin Page" 事件。
*   用戶登出時，成功記錄 "User Logout" 事件。

## 4. 結論

透過實作審計日誌功能，MorningAI MVP 專案能夠追蹤和記錄系統中的關鍵用戶活動，這對於安全監控、故障排除和滿足合規性要求提供了重要的基礎。這些日誌將有助於識別潛在的安全威脅和分析用戶行為。

