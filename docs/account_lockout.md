# 帳戶鎖定機制實作總結報告

## 1. 概述

本報告總結了為 MorningAI MVP 專案實作帳戶鎖定機制（Account Lockout）的過程和結果。此功能旨在透過限制失敗登入嘗試次數，防止暴力破解攻擊，從而增強應用程式的安全性。

## 2. 實作細節

### 2.1. 設計考量

帳戶鎖定機制主要基於 Redis 快取實現，利用其快速讀寫和設定過期時間（TTL）的特性。設計中考慮了以下關鍵參數：

*   **最大登入嘗試次數 (MAX_LOGIN_ATTEMPTS)**：設定為 5 次。
*   **登入嘗試視窗時間 (LOGIN_ATTEMPT_WINDOW_SECONDS)**：設定為 300 秒（5 分鐘）。在此時間窗內，失敗的登入嘗試會被計數。
*   **帳戶鎖定持續時間 (ACCOUNT_LOCKOUT_DURATION_SECONDS)**：設定為 900 秒（15 分鐘）。帳戶被鎖定後，在此期間內無法登入。

### 2.2. 資料模型 (Redis)

在 Redis 中，使用了兩個主要鍵來追蹤和管理帳戶鎖定狀態：

*   `login_attempts:{user_id}`：儲存特定用戶的失敗登入嘗試次數。此鍵在首次失敗嘗試時設定 TTL 為 `LOGIN_ATTEMPT_WINDOW_SECONDS`。
*   `account_locked:{user_id}`：標記特定用戶的帳戶是否被鎖定。此鍵在帳戶被鎖定時設定 TTL 為 `ACCOUNT_LOCKOUT_DURATION_SECONDS`。

### 2.3. 核心功能

*   **`authenticate_user(username, password)`**：
    *   在驗證密碼前，檢查帳戶是否已被鎖定。如果鎖定，則返回相應的錯誤訊息和剩餘鎖定時間。
    *   如果密碼驗證失敗，則遞增 `login_attempts` 計數器。如果計數器達到 `MAX_LOGIN_ATTEMPTS`，則呼叫 `lock_account` 函數鎖定帳戶。
    *   如果密碼驗證成功，則呼叫 `reset_login_attempts` 函數清除所有相關的 Redis 鍵，重置嘗試次數和鎖定狀態。

*   **`increment_login_attempts(user_id)`**：遞增用戶的失敗登入嘗試次數。如果這是首次嘗試，則設定嘗試次數鍵的 TTL。

*   **`reset_login_attempts(user_id)`**：清除用戶的 `login_attempts` 和 `account_locked` 鍵，將帳戶恢復到未鎖定狀態。

*   **`lock_account(user_id)`**：設定 `account_locked` 鍵，並設定其 TTL 為 `ACCOUNT_LOCKOUT_DURATION_SECONDS`。

*   **`is_account_locked(user_id)`**：檢查 `account_locked` 鍵是否存在且未過期，以判斷帳戶是否被鎖定，並返回剩餘鎖定時間。

### 2.4. 程式碼修改

主要修改集中在 `apps/api/src/auth.py` 中，增加了帳戶鎖定相關的常數和函數，並修改了 `authenticate_user` 函數以整合這些邏輯。同時，在 `apps/api/src/main.py` 中，`login` 路由被更新以處理 `authenticate_user` 函數回傳的帳戶鎖定訊息。為了測試方便，還增加了管理員端點 `/auth/admin/clear-lockout-keys` 和 `/auth/admin/get-user-id/<username>`。

## 3. 測試結果

透過 `test_account_lockout.py` 測試腳本，驗證了帳戶鎖定機制的以下行為：

1.  **初始狀態**：確保用戶在測試前處於未鎖定狀態，且可以成功登入。
2.  **失敗登入嘗試**：連續使用錯誤密碼登入，每次嘗試都會正確顯示剩餘嘗試次數。
3.  **帳戶鎖定觸發**：當失敗登入嘗試次數達到 `MAX_LOGIN_ATTEMPTS` 時，帳戶被鎖定，並返回相應的鎖定訊息。
4.  **鎖定期間拒絕登入**：在帳戶鎖定期間，即使使用正確密碼也無法登入，並返回鎖定訊息。
5.  **鎖定過期後解鎖**：等待鎖定時間過期後，用戶可以再次使用正確密碼成功登入，且失敗嘗試計數器被重置。

所有測試案例均成功通過，證明帳戶鎖定機制按預期工作。

## 4. 結論與下一步建議

帳戶鎖定機制已成功實作並經過驗證，有效提升了應用程式的安全性，抵禦暴力破解攻擊。這完成了「短期改進」中的第二項任務。

接下來，我們將繼續按照「短期改進」的路線圖，實作以下功能：

1.  **電子郵件驗證**：添加電子郵件驗證流程。

這將進一步增強用戶帳戶的安全性和可靠性。

--- 

**作者**：Manus AI
**日期**：2025年9月16日
