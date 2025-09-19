"""
簡化的 API 文檔端點
提供基本的 API 文檔頁面
"""

from flask import Blueprint, render_template_string

simple_docs_bp = Blueprint('simple_docs', __name__)

# 簡單的 HTML 文檔模板
DOCS_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MorningAI MVP API 文檔</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
        .endpoint { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007cba; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 3px; color: white; font-weight: bold; margin-right: 10px; }
        .get { background: #61affe; }
        .post { background: #49cc90; }
        .put { background: #fca130; }
        .delete { background: #f93e3e; }
        .code { background: #f4f4f4; padding: 10px; border-radius: 3px; font-family: monospace; }
        .status-ok { color: #28a745; }
        .status-error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌅 MorningAI MVP API 文檔</h1>
        <p>版本: 1.0.0 | 基礎 URL: <code>https://morningai-mvp.onrender.com</code></p>
        <p><strong>狀態:</strong> <span class="status-ok">✅ 服務運行中</span></p>
    </div>

    <h2>🔐 認證</h2>
    <p>大部分 API 端點需要 JWT Token 認證。在請求標頭中包含:</p>
    <div class="code">Authorization: Bearer &lt;your_jwt_token&gt;</div>

    <h2>📋 API 端點</h2>

    <div class="endpoint">
        <span class="method get">GET</span><strong>/health</strong>
        <p>健康檢查端點，檢查服務狀態</p>
        <div class="code">
curl https://morningai-mvp.onrender.com/health
        </div>
        <p><strong>回應:</strong> <code>{"ok": true, "message": "Service is healthy"}</code></p>
    </div>

    <div class="endpoint">
        <span class="method post">POST</span><strong>/api/register</strong>
        <p>用戶註冊</p>
        <div class="code">
curl -X POST https://morningai-mvp.onrender.com/api/register \\
  -H "Content-Type: application/json" \\
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
        </div>
    </div>

    <div class="endpoint">
        <span class="method post">POST</span><strong>/api/login</strong>
        <p>用戶登入，獲取 JWT Token</p>
        <div class="code">
curl -X POST https://morningai-mvp.onrender.com/api/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "test@example.com", "password": "password123"}'
        </div>
    </div>

    <div class="endpoint">
        <span class="method get">GET</span><strong>/api/profile</strong> 🔒
        <p>獲取當前用戶資料（需要認證）</p>
        <div class="code">
curl https://morningai-mvp.onrender.com/api/profile \\
  -H "Authorization: Bearer &lt;your_jwt_token&gt;"
        </div>
    </div>

    <div class="endpoint">
        <span class="method post">POST</span><strong>/api/auth/logout</strong> 🔒
        <p>用戶登出，將 Token 加入黑名單（需要認證）</p>
        <div class="code">
curl -X POST https://morningai-mvp.onrender.com/api/auth/logout \\
  -H "Authorization: Bearer &lt;your_jwt_token&gt;"
        </div>
    </div>

    <div class="endpoint">
        <span class="method get">GET</span><strong>/api/admin/users</strong> 🔒👑
        <p>獲取用戶列表（需要管理員權限）</p>
        <div class="code">
curl https://morningai-mvp.onrender.com/api/admin/users \\
  -H "Authorization: Bearer &lt;admin_jwt_token&gt;"
        </div>
    </div>

    <h2>📊 狀態碼</h2>
    <ul>
        <li><span class="status-ok">200</span> - 成功</li>
        <li><span class="status-error">400</span> - 請求錯誤</li>
        <li><span class="status-error">401</span> - 未認證或 Token 無效</li>
        <li><span class="status-error">403</span> - 權限不足</li>
        <li><span class="status-error">404</span> - 端點不存在</li>
        <li><span class="status-error">500</span> - 服務器錯誤</li>
    </ul>

    <h2>🔒 安全特性</h2>
    <ul>
        <li><strong>JWT 認證:</strong> 使用 JSON Web Tokens 進行用戶認證</li>
        <li><strong>JWT 黑名單:</strong> 登出後的 Token 會被加入黑名單，無法再次使用</li>
        <li><strong>RBAC:</strong> 基於角色的訪問控制</li>
        <li><strong>RLS:</strong> 資料庫行級安全政策</li>
        <li><strong>2FA:</strong> 支援雙因素認證（可選）</li>
    </ul>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
        <p>© 2025 MorningAI MVP | 最後更新: 2025-09-20</p>
    </footer>
</body>
</html>
"""

@simple_docs_bp.route('/docs')
def api_docs():
    """API 文檔頁面"""
    return render_template_string(DOCS_TEMPLATE)

@simple_docs_bp.route('/docs/')
def api_docs_slash():
    """API 文檔頁面（帶斜線）"""
    return render_template_string(DOCS_TEMPLATE)
