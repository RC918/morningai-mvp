# JWT 黑名單回歸測試套件

## 概述

這個文檔描述了 JWT 黑名單功能的回歸測試套件，用於防止該關鍵安全功能在未來版本中退化。

## 測試目標

確保以下 JWT 黑名單功能在任何程式碼變更後都能正常運作：

1. **基本登出功能**：用戶登出後，其 JWT token 應立即失效
2. **登出所有設備功能**：用戶可以撤銷所有設備上的 token
3. **黑名單持久性**：黑名單項目正確儲存在資料庫中
4. **管理員功能**：管理員可以查看和管理黑名單

## 關鍵回歸測試案例

### 測試案例 1: 基本登出功能

**目的**：確保登出後的 token 無法存取受保護的端點

**步驟**：
1. 用戶登入獲取 JWT token
2. 使用 token 存取受保護的端點（應該成功）
3. 執行登出操作
4. 再次使用相同的 token 存取受保護的端點（應該失敗）

**預期結果**：
- 登出前：token 有效，可以存取受保護的端點
- 登出後：token 失效，返回 401 錯誤，錯誤訊息包含 "revoked"

**關鍵驗證點**：
```bash
# 登出後的 token 應該返回 401 錯誤
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/user
# 預期回應：{"message": "Token has been revoked"}
```

### 測試案例 2: 登出所有設備功能

**目的**：確保「登出所有設備」功能能撤銷用戶的所有 token

**步驟**：
1. 同一用戶多次登入，獲取多個 JWT token
2. 驗證所有 token 都有效
3. 使用其中一個 token 執行「登出所有設備」操作
4. 驗證所有 token 都已失效

**預期結果**：
- 執行「登出所有設備」前：所有 token 都有效
- 執行「登出所有設備」後：所有 token 都失效

**關鍵驗證點**：
```bash
# 所有 token 都應該返回 401 錯誤
for token in token1 token2 token3; do
    curl -H "Authorization: Bearer $token" http://localhost:5000/api/user
done
# 預期：所有請求都返回 401 錯誤
```

### 測試案例 3: 黑名單持久性

**目的**：確保黑名單項目正確儲存在資料庫中

**步驟**：
1. 用戶登入並登出
2. 檢查資料庫中的 `jwt_blacklist` 表
3. 驗證黑名單項目包含必要的欄位

**預期結果**：
- 資料庫中應該有對應的黑名單記錄
- 記錄應包含：`jti`、`user_id`、`expires_at`、`created_at`

**關鍵驗證點**：
```sql
-- 檢查黑名單項目
SELECT jti, user_id, expires_at, created_at 
FROM jwt_blacklist 
WHERE user_id = <user_id>
ORDER BY created_at DESC;
```

## 自動化測試腳本

### 快速驗證腳本

建立一個簡單的 bash 腳本來快速驗證 JWT 黑名單功能：

```bash
#!/bin/bash
# jwt_blacklist_quick_test.sh

echo "🔍 JWT 黑名單快速回歸測試"
echo "================================"

# 設定 API 基礎 URL
API_BASE="http://localhost:5000"

# 測試 1: 基本登出功能
echo "📝 測試 1: 基本登出功能"

# 登入
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ 登入失敗"
    exit 1
fi

echo "✅ 登入成功，獲得 token"

# 驗證 token 有效
USER_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/api/user")

if [ "$USER_RESPONSE" != "200" ]; then
    echo "❌ Token 驗證失敗"
    exit 1
fi

echo "✅ Token 驗證成功"

# 登出
LOGOUT_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -X POST -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/api/auth/logout")

if [ "$LOGOUT_RESPONSE" != "200" ]; then
    echo "❌ 登出失敗"
    exit 1
fi

echo "✅ 登出成功"

# 驗證 token 已失效
REVOKED_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/api/user")

if [ "$REVOKED_RESPONSE" = "200" ]; then
    echo "❌ 嚴重錯誤：登出後的 token 仍然有效！"
    exit 1
elif [ "$REVOKED_RESPONSE" = "401" ]; then
    echo "✅ 關鍵測試通過：token 已被正確撤銷"
else
    echo "❌ 意外的回應狀態碼: $REVOKED_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 JWT 黑名單回歸測試通過！"
echo "✅ JWT 黑名單功能沒有退化"
```

### CI/CD 集成

在 GitHub Actions 中添加回歸測試：

```yaml
# .github/workflows/jwt-blacklist-regression.yml
name: JWT Blacklist Regression Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  jwt-blacklist-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd apps/api
        pip install -r requirements.txt
    
    - name: Start API server
      run: |
        cd apps/api
        python src/main.py &
        sleep 10
    
    - name: Run JWT Blacklist Regression Test
      run: |
        cd apps/api
        chmod +x jwt_blacklist_quick_test.sh
        ./jwt_blacklist_quick_test.sh
    
    - name: Stop API server
      run: pkill -f "python src/main.py"
```

## 測試檢查清單

在每次發布前，請確保以下項目都通過：

- [ ] **基本登出功能**：登出後的 token 無法存取受保護的端點
- [ ] **登出所有設備功能**：所有用戶的 token 都被撤銷
- [ ] **黑名單持久性**：黑名單項目正確儲存在資料庫中
- [ ] **管理員功能**：管理員可以查看黑名單
- [ ] **錯誤處理**：無效的 token 返回適當的錯誤訊息
- [ ] **效能測試**：大量並發登出不會導致系統問題

## 故障排除

### 常見問題

1. **Token 仍然有效**
   - 檢查 `decorators.py` 中的 `token_required` 裝飾器
   - 確認 `datetime` 模組正確導入
   - 驗證 `is_blacklisted` 函數的邏輯

2. **黑名單項目未儲存**
   - 檢查 `add_to_blacklist` 函數
   - 確認資料庫連接正常
   - 驗證 `db.session.commit()` 被調用

3. **登出所有設備失敗**
   - 檢查 `tokens_valid_since` 欄位更新
   - 確認 JWT 中包含 `iat` 聲明
   - 驗證時間戳比較邏輯

### 調試命令

```bash
# 檢查黑名單表內容
sqlite3 instance/app.db "SELECT * FROM jwt_blacklist;"

# 檢查用戶的 tokens_valid_since
sqlite3 instance/app.db "SELECT username, tokens_valid_since FROM users;"

# 測試 JWT 解碼
python -c "
import jwt
token = 'your_token_here'
decoded = jwt.decode(token, options={'verify_signature': False})
print(decoded)
"
```

## 維護指南

1. **定期執行**：每週執行一次完整的回歸測試
2. **程式碼變更後**：任何涉及認證或授權的變更後都要執行
3. **發布前**：每次發布前必須執行並通過所有測試
4. **監控**：在生產環境中監控登出功能的成功率

## 結論

這個回歸測試套件確保 JWT 黑名單功能的穩定性和安全性。定期執行這些測試可以及早發現問題，防止安全漏洞進入生產環境。

**重要提醒**：JWT 黑名單是關鍵的安全功能，任何相關的測試失敗都應該被視為高優先級問題並立即修復。
