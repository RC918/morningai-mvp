-- RLS 政策測試腳本
-- 此腳本用於驗證 RLS 政策是否正確實施

-- 創建測試用戶（如果不存在）
DO $$
BEGIN
    -- 創建測試用戶 1
    IF NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'test1@example.com') THEN
        INSERT INTO "user" (username, email, password_hash, role, is_active, is_email_verified)
        VALUES ('testuser1', 'test1@example.com', 'hashed_password_1', 'user', true, true);
    END IF;
    
    -- 創建測試用戶 2
    IF NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'test2@example.com') THEN
        INSERT INTO "user" (username, email, password_hash, role, is_active, is_email_verified)
        VALUES ('testuser2', 'test2@example.com', 'hashed_password_2', 'user', true, true);
    END IF;
    
    -- 創建測試管理員
    IF NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'admin@example.com') THEN
        INSERT INTO "user" (username, email, password_hash, role, is_active, is_email_verified)
        VALUES ('admin', 'admin@example.com', 'hashed_password_admin', 'admin', true, true);
    END IF;
END $$;

-- 測試 RLS 政策的函數
CREATE OR REPLACE FUNCTION test_rls_policies()
RETURNS TABLE (
    test_name text,
    expected_result text,
    actual_result text,
    status text
) AS $$
DECLARE
    test_user1_id uuid;
    test_user2_id uuid;
    admin_user_id uuid;
    policy_count integer;
BEGIN
    -- 獲取測試用戶 ID
    SELECT id INTO test_user1_id FROM "user" WHERE email = 'test1@example.com';
    SELECT id INTO test_user2_id FROM "user" WHERE email = 'test2@example.com';
    SELECT id INTO admin_user_id FROM "user" WHERE email = 'admin@example.com';
    
    -- 測試 1: 檢查 RLS 是否已啟用
    SELECT COUNT(*) INTO policy_count 
    FROM pg_policies 
    WHERE tablename = 'user' AND schemaname = 'public';
    
    RETURN QUERY SELECT 
        'RLS Policies Count'::text,
        'At least 5 policies'::text,
        policy_count::text,
        CASE WHEN policy_count >= 5 THEN 'PASS' ELSE 'FAIL' END;
    
    -- 測試 2: 檢查表格是否啟用了 RLS
    RETURN QUERY SELECT 
        'User Table RLS Enabled'::text,
        'true'::text,
        (SELECT relrowsecurity::text FROM pg_class WHERE relname = 'user'),
        CASE WHEN (SELECT relrowsecurity FROM pg_class WHERE relname = 'user') THEN 'PASS' ELSE 'FAIL' END;
    
    -- 測試 3: 檢查安全函數是否存在
    RETURN QUERY SELECT 
        'Security Functions Exist'::text,
        'true'::text,
        (SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'user_has_role'))::text,
        CASE WHEN EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'user_has_role') THEN 'PASS' ELSE 'FAIL' END;
    
    -- 測試 4: 檢查政策是否正確創建
    RETURN QUERY SELECT 
        'User View Own Profile Policy'::text,
        'true'::text,
        (SELECT EXISTS(SELECT 1 FROM pg_policies WHERE tablename = 'user' AND policyname = 'Users can view own profile'))::text,
        CASE WHEN EXISTS(SELECT 1 FROM pg_policies WHERE tablename = 'user' AND policyname = 'Users can view own profile') THEN 'PASS' ELSE 'FAIL' END;
    
    RETURN QUERY SELECT 
        'Admin View All Users Policy'::text,
        'true'::text,
        (SELECT EXISTS(SELECT 1 FROM pg_policies WHERE tablename = 'user' AND policyname = 'Admins can view all users'))::text,
        CASE WHEN EXISTS(SELECT 1 FROM pg_policies WHERE tablename = 'user' AND policyname = 'Admins can view all users') THEN 'PASS' ELSE 'FAIL' END;
    
END;
$$ LANGUAGE plpgsql;

-- 執行測試
SELECT * FROM test_rls_policies();

-- 清理測試函數
DROP FUNCTION IF EXISTS test_rls_policies();

-- 顯示所有已創建的 RLS 政策
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
