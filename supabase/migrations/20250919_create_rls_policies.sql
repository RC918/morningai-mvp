-- 創建 RLS 政策遷移
-- 此遷移為所有主要表格啟用 Row Level Security (RLS) 並創建適當的政策

-- 啟用 RLS 對 user 表格
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;

-- 用戶只能查看和更新自己的資料
CREATE POLICY "Users can view own profile" ON "user"
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON "user"
    FOR UPDATE USING (auth.uid()::text = id::text);

-- 管理員可以查看所有用戶
CREATE POLICY "Admins can view all users" ON "user"
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );

-- 管理員可以更新所有用戶
CREATE POLICY "Admins can update all users" ON "user"
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM "user" 
            WHERE id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );

-- 允許用戶註冊（插入新用戶）
CREATE POLICY "Allow user registration" ON "user"
    FOR INSERT WITH CHECK (true);

-- 如果存在 tenant 表格，啟用 RLS
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenant') THEN
        ALTER TABLE "tenant" ENABLE ROW LEVEL SECURITY;
        
        -- 用戶只能查看自己所屬的租戶
        CREATE POLICY "Users can view own tenant" ON "tenant"
            FOR SELECT USING (
                EXISTS (
                    SELECT 1 FROM "user" 
                    WHERE id::text = auth.uid()::text 
                    AND tenant_id = "tenant".id
                )
            );
        
        -- 租戶管理員可以更新租戶資訊
        CREATE POLICY "Tenant admins can update tenant" ON "tenant"
            FOR UPDATE USING (
                EXISTS (
                    SELECT 1 FROM "user" 
                    WHERE id::text = auth.uid()::text 
                    AND tenant_id = "tenant".id
                    AND (role = 'admin' OR role = 'tenant_admin')
                )
            );
    END IF;
END $$;

-- 如果存在 jwt_blacklist 表格，啟用 RLS
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'jwt_blacklist') THEN
        ALTER TABLE "jwt_blacklist" ENABLE ROW LEVEL SECURITY;
        
        -- 只有系統可以管理 JWT 黑名單（通過服務角色）
        CREATE POLICY "Service role can manage jwt blacklist" ON "jwt_blacklist"
            FOR ALL USING (auth.role() = 'service_role');
        
        -- 用戶可以查看自己的被撤銷的 token（可選）
        CREATE POLICY "Users can view own blacklisted tokens" ON "jwt_blacklist"
            FOR SELECT USING (
                user_id IS NOT NULL AND 
                user_id::text = auth.uid()::text
            );
    END IF;
END $$;

-- 如果存在 audit_log 表格，啟用 RLS
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_log') THEN
        ALTER TABLE "audit_log" ENABLE ROW LEVEL SECURITY;
        
        -- 用戶只能查看自己的審計日誌
        CREATE POLICY "Users can view own audit logs" ON "audit_log"
            FOR SELECT USING (
                user_id IS NOT NULL AND 
                user_id::text = auth.uid()::text
            );
        
        -- 管理員可以查看所有審計日誌
        CREATE POLICY "Admins can view all audit logs" ON "audit_log"
            FOR SELECT USING (
                EXISTS (
                    SELECT 1 FROM "user" 
                    WHERE id::text = auth.uid()::text 
                    AND role = 'admin'
                )
            );
        
        -- 系統可以插入審計日誌
        CREATE POLICY "Service role can insert audit logs" ON "audit_log"
            FOR INSERT WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

-- 創建安全函數來檢查用戶權限
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

-- 創建函數來檢查用戶是否為租戶管理員
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

-- 創建函數來獲取當前用戶的租戶 ID
CREATE OR REPLACE FUNCTION auth.current_user_tenant_id()
RETURNS uuid AS $$
BEGIN
    RETURN (
        SELECT tenant_id FROM "user" 
        WHERE id::text = auth.uid()::text
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 添加註釋說明 RLS 政策
COMMENT ON POLICY "Users can view own profile" ON "user" IS 'RLS: 用戶只能查看自己的個人資料';
COMMENT ON POLICY "Users can update own profile" ON "user" IS 'RLS: 用戶只能更新自己的個人資料';
COMMENT ON POLICY "Admins can view all users" ON "user" IS 'RLS: 管理員可以查看所有用戶';
COMMENT ON POLICY "Admins can update all users" ON "user" IS 'RLS: 管理員可以更新所有用戶';
COMMENT ON POLICY "Allow user registration" ON "user" IS 'RLS: 允許新用戶註冊';

-- 記錄遷移完成
INSERT INTO public.schema_migrations (version, applied_at) 
VALUES ('20250919_create_rls_policies', NOW())
ON CONFLICT (version) DO NOTHING;
