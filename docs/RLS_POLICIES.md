# Row Level Security (RLS) 政策文檔

## 概述

本文檔描述了 MorningAI MVP 專案中實施的 Row Level Security (RLS) 政策。RLS 是 PostgreSQL 的一個安全功能，允許在資料庫層面控制用戶對資料行的存取權限。

## 實施的 RLS 政策

### 1. User 表格政策

#### 基本原則
- 用戶只能查看和更新自己的個人資料
- 管理員可以查看和更新所有用戶資料
- 允許新用戶註冊

#### 具體政策

**用戶查看自己的資料**
```sql
CREATE POLICY "Users can view own profile" ON "user"
    FOR SELECT USING (auth.uid()::text = id::text);
```

**用戶更新自己的資料**
```sql
CREATE POLICY "Users can update own profile" ON "user"
    FOR UPDATE USING (auth.uid()::text = id::text);
```

**管理員查看所有用戶**
```sql
CREATE POLICY "Admins can view all users" ON "user"
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );
```

**管理員更新所有用戶**
```sql
CREATE POLICY "Admins can update all users" ON "user"
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );
```

**允許用戶註冊**
```sql
CREATE POLICY "Allow user registration" ON "user"
    FOR INSERT WITH CHECK (true);
```

### 2. Tenant 表格政策（如果存在）

#### 基本原則
- 用戶只能查看自己所屬的租戶
- 租戶管理員可以更新租戶資訊

#### 具體政策

**用戶查看自己的租戶**
```sql
CREATE POLICY "Users can view own tenant" ON "tenant"
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND tenant_id = "tenant".id
        )
    );
```

**租戶管理員更新租戶**
```sql
CREATE POLICY "Tenant admins can update tenant" ON "tenant"
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND tenant_id = "tenant".id
            AND (role = 'admin' OR role = 'tenant_admin')
        )
    );
```

### 3. JWT Blacklist 表格政策（如果存在）

#### 基本原則
- 只有服務角色可以管理 JWT 黑名單
- 用戶可以查看自己被撤銷的 token

#### 具體政策

**服務角色管理黑名單**
```sql
CREATE POLICY "Service role can manage jwt blacklist" ON "jwt_blacklist"
    FOR ALL USING (auth.role() = 'service_role');
```

**用戶查看自己的黑名單 token**
```sql
CREATE POLICY "Users can view own blacklisted tokens" ON "jwt_blacklist"
    FOR SELECT USING (
        user_id IS NOT NULL AND 
        user_id::text = auth.uid()::text
    );
```

### 4. Audit Log 表格政策（如果存在）

#### 基本原則
- 用戶只能查看自己的審計日誌
- 管理員可以查看所有審計日誌
- 系統可以插入審計日誌

#### 具體政策

**用戶查看自己的審計日誌**
```sql
CREATE POLICY "Users can view own audit logs" ON "audit_log"
    FOR SELECT USING (
        user_id IS NOT NULL AND 
        user_id::text = auth.uid()::text
    );
```

**管理員查看所有審計日誌**
```sql
CREATE POLICY "Admins can view all audit logs" ON "audit_log"
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );
```

**系統插入審計日誌**
```sql
CREATE POLICY "Service role can insert audit logs" ON "audit_log"
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
```

## 安全輔助函數

### 1. 檢查用戶角色
```sql
CREATE OR REPLACE FUNCTION auth.user_has_role(required_role text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM "user" 
        WHERE id::text = auth.uid()::text 
        AND role = required_role
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 2. 檢查租戶管理員權限
```sql
CREATE OR REPLACE FUNCTION auth.user_is_tenant_admin(tenant_uuid uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM "user" 
        WHERE id::text = auth.uid()::text 
        AND tenant_id = tenant_uuid
        AND (role = 'admin' OR role = 'tenant_admin')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 3. 獲取當前用戶租戶 ID
```sql
CREATE OR REPLACE FUNCTION auth.current_user_tenant_id()
RETURNS uuid AS $$
BEGIN
    RETURN (
        SELECT tenant_id FROM "user" 
        WHERE id::text = auth.uid()::text
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## 測試和驗證

### 測試腳本
專案包含了 RLS 政策的測試腳本 `20250919_test_rls_policies.sql`，用於驗證：

1. RLS 政策數量是否正確
2. 表格是否啟用了 RLS
3. 安全函數是否存在
4. 具體政策是否正確創建

### 執行測試
```sql
-- 在 Supabase 或 PostgreSQL 中執行
\i supabase/migrations/20250919_test_rls_policies.sql
```

## 部署說明

### 1. 本地開發環境
```bash
# 使用 Supabase CLI 應用遷移
supabase db reset
supabase migration up
```

### 2. 生產環境
```bash
# 推送遷移到遠端 Supabase 專案
supabase db push
```

### 3. 手動執行
如果需要手動執行，可以直接在 Supabase Dashboard 的 SQL Editor 中執行遷移檔案內容。

## 安全考量

### 1. 服務角色使用
- 後端應用程式應使用 `service_role` 金鑰來繞過 RLS 限制
- 前端應用程式應使用 `anon` 或已驗證用戶的 JWT

### 2. JWT 驗證
- 所有 RLS 政策都依賴於 `auth.uid()` 函數
- 確保 JWT 正確設置並包含用戶 ID

### 3. 角色管理
- 管理員角色具有較高權限，需要謹慎分配
- 租戶管理員只能管理自己租戶內的資源

## 監控和維護

### 1. 政策效能
- 定期檢查 RLS 政策的查詢效能
- 為相關欄位添加適當的索引

### 2. 審計
- 使用 audit_log 表格記錄重要操作
- 定期檢查異常的存取模式

### 3. 更新
- 當添加新表格時，記得實施相應的 RLS 政策
- 定期檢查和更新安全政策

## 故障排除

### 1. 常見問題
- **無法查看資料**: 檢查 JWT 是否正確設置
- **權限不足**: 確認用戶角色和政策條件
- **政策衝突**: 檢查多個政策之間的邏輯關係

### 2. 調試工具
```sql
-- 檢查當前用戶
SELECT auth.uid(), auth.role();

-- 檢查政策狀態
SELECT * FROM pg_policies WHERE schemaname = 'public';

-- 檢查 RLS 啟用狀態
SELECT relname, relrowsecurity FROM pg_class WHERE relname IN ('user', 'tenant', 'jwt_blacklist', 'audit_log');
```

## 版本歷史

- **v1.0** (2025-09-19): 初始 RLS 政策實施
  - User 表格基本政策
  - Tenant 表格政策（條件性）
  - JWT Blacklist 政策（條件性）
  - Audit Log 政策（條件性）
  - 安全輔助函數
