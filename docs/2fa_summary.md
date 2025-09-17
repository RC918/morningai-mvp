# 雙因素驗證 (2FA) 實作摘要

## 1. 概述

本文件概述了 MorningAI MVP 專案中雙因素驗證 (2FA) 功能的實作細節。2FA 透過要求用戶提供兩種不同類型的憑證來驗證身份，顯著提升了帳戶安全性。考量到專案已使用 Supabase 進行身份驗證和資料庫管理，本次實作主要利用了 Supabase 內建的 MFA 功能。

## 2. 實作方法

2FA 的實作主要圍繞 Supabase 的多因素驗證 (MFA) API 進行，並整合到現有的 Flask 後端服務中。具體步驟如下：

### 2.1. Supabase MFA API 整合

*   **API 端點**：在 `auth.py` 中定義了與 Supabase MFA 相關的函數，包括 `supabase_mfa_enroll`、`supabase_mfa_challenge`、`supabase_mfa_verify`、`supabase_mfa_unenroll` 和 `supabase_mfa_list_factors`。這些函數負責與 Supabase 的 MFA 服務進行互動。
*   **Flask 路由**：在 `main.py` 中添加了對應的 Flask 路由 (`/auth/mfa/enroll`, `/auth/mfa/challenge`, `/auth/mfa/verify`, `/auth/mfa/unenroll`, `/auth/mfa/factors`)，用於處理前端發送的 MFA 相關請求。這些路由會呼叫 `auth.py` 中對應的 Supabase MFA 函數。
*   **環境變數**：確保 `.env` 檔案中配置了 `SUPABASE_PROJECT_REF` 和 `SUPABASE_ANON_KEY`，以便 Flask 應用程式能夠正確連接 Supabase 服務。

### 2.2. 註冊/登入流程修改

*   **MFA 啟用與註冊**：用戶可以透過呼叫 `/auth/mfa/enroll` 端點來啟用 MFA 並註冊 MFA 設備（例如 Google Authenticator）。此過程會生成一個 QR Code 供用戶掃描。
*   **MFA 挑戰與驗證**：在用戶登入後，如果已啟用 MFA，應用程式會要求用戶提供 TOTP 應用程式生成的一次性密碼。用戶透過 `/auth/mfa/challenge` 獲取挑戰，然後透過 `/auth/mfa/verify` 提交驗證碼。

## 3. 測試

2FA 功能的測試是中期改進測試的一部分，確保了 MFA 註冊、挑戰和驗證流程的正確性。測試涵蓋了以下場景：

*   用戶成功註冊 MFA 設備。
*   用戶成功通過 MFA 挑戰並驗證。
*   MFA 驗證失敗時的錯誤處理。

## 4. 結論

透過整合 Supabase 內建的 MFA 功能，MorningAI MVP 專案成功實作了雙因素驗證，顯著提升了用戶帳戶的安全性。這為後續更高級別的安全措施奠定了基礎。

