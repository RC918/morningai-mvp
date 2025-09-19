# 零停機資料庫升級 SOP

## 概述

本文件定義了 `morningai-mvp` 專案的零停機資料庫升級標準作業程序，遵循「expand → code → contract」三階段策略。

## 三階段升級策略

### 階段 1: Expand（擴展）
**目標**: 添加新的資料庫結構，不刪除舊的

**允許的操作**:
- 添加新表格
- 添加新欄位（必須是 `nullable` 或有 `default` 值）
- 添加新索引
- 創建新的 stored procedures/functions

**禁止的操作**:
- 刪除任何現有結構
- 修改現有欄位的類型或約束
- 重命名表格或欄位

**範例**:
```sql
-- ✅ 正確：添加新欄位
ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL;

-- ✅ 正確：添加新索引
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);

-- ❌ 錯誤：刪除欄位
ALTER TABLE users DROP COLUMN old_field;
```

### 階段 2: Code（程式碼部署）
**目標**: 部署應用程式以使用新的資料庫結構

**步驟**:
1. 部署新版本應用程式
2. 應用程式開始讀寫新欄位
3. 執行資料遷移（backfill）
4. 驗證新功能正常運作

**資料遷移範例**:
```sql
-- 分批更新，避免長時間鎖表
UPDATE users 
SET phone = legacy_phone_field 
WHERE phone IS NULL 
  AND id BETWEEN 1 AND 1000;
```

### 階段 3: Contract（收縮）
**目標**: 清理不再需要的舊結構

**前置條件**:
- 新功能已穩定運行至少 24 小時
- 確認沒有應用程式仍在使用舊結構
- 已完成資料遷移和驗證

**操作**:
```sql
-- 移除舊欄位
ALTER TABLE users DROP COLUMN legacy_phone_field;

-- 移除舊索引
DROP INDEX IF EXISTS idx_users_legacy_phone;
```

## 風險控制措施

### 長交易預防
```sql
-- 設定語句超時
SET statement_timeout = '60s';

-- 分批處理大量更新
DO $$
DECLARE
    batch_size INTEGER := 1000;
    affected_rows INTEGER;
BEGIN
    LOOP
        UPDATE users 
        SET phone = legacy_phone_field 
        WHERE phone IS NULL 
          AND id IN (
              SELECT id FROM users 
              WHERE phone IS NULL 
              LIMIT batch_size
          );
        
        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        EXIT WHEN affected_rows = 0;
        
        -- 短暫暫停，釋放鎖定
        PERFORM pg_sleep(0.1);
    END LOOP;
END $$;
```

### 索引建立
```sql
-- 使用 CONCURRENTLY 避免鎖表
CREATE INDEX CONCURRENTLY idx_users_email_active 
ON users(email) WHERE active = true;
```

### 表鎖避免
- 避免在高峰時段執行 DDL 操作
- 使用 `LOCK TIMEOUT` 設定
- 監控 `pg_locks` 視圖

## 回滾策略

### 自動回滾觸發條件
- 部署後 5 分鐘內錯誤率超過 5%
- 資料庫連線數超過 80%
- 關鍵 API 端點回應時間超過 2 秒

### 回滾步驟
1. **立即**: 回滾應用程式到前一版本
2. **評估**: 檢查資料庫狀態
3. **決策**: 是否需要回滾資料庫變更
4. **執行**: 如需要，執行 Alembic downgrade

### 回滾命令
```bash
# 應用程式回滾
git checkout v0.7.0
docker-compose up -d

# 資料庫回滾（如需要）
cd apps/api
alembic downgrade -1
```

## 部署檢查清單

### 部署前
- [ ] 已執行 `alembic upgrade head --sql` 生成 SQL 預覽
- [ ] 已在 staging 環境測試完整流程
- [ ] 已準備回滾腳本
- [ ] 已通知相關團隊維護時間
- [ ] 已設定監控告警

### 部署中
- [ ] 監控資料庫連線數
- [ ] 監控應用程式錯誤率
- [ ] 監控關鍵 API 回應時間
- [ ] 檢查日誌是否有異常

### 部署後
- [ ] 驗證新功能正常運作
- [ ] 檢查資料完整性
- [ ] 確認效能指標正常
- [ ] 更新文件和 Release Notes

## 常見問題處理

### Supabase RLS 相關
```sql
-- 啟用 RLS 前先測試政策
SELECT * FROM users WHERE auth.uid() = id;

-- 漸進式啟用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- 測試後再添加限制性政策
```

### 連線池問題
- 檢查 pgbouncer 設定
- 監控 `pool_mode` 設定
- 避免長時間持有連線

### 效能監控
```sql
-- 檢查慢查詢
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- 檢查索引使用情況
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

## 緊急聯絡

- **資料庫管理員**: [聯絡資訊]
- **DevOps 團隊**: [聯絡資訊]
- **產品負責人**: [聯絡資訊]

---

**最後更新**: 2025-09-20  
**版本**: 1.0  
**負責人**: Manus AI
