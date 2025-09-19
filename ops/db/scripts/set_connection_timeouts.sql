-- Phase-DB.0: 設定連線超時以避免長交易卡表鎖
-- 執行前請確認資料庫名稱

-- 設定語句超時為 60 秒
ALTER DATABASE morningai_mvp SET statement_timeout = '60s';

-- 設定鎖定超時為 5 秒
ALTER DATABASE morningai_mvp SET lock_timeout = '5s';

-- 檢查設定是否生效
SELECT name, setting, unit, context 
FROM pg_settings 
WHERE name IN ('statement_timeout', 'lock_timeout');

-- 備註: 請將 'morningai_mvp' 替換為實際的資料庫名稱
