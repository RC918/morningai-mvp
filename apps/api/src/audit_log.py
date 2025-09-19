# apps/api/src/audit_log.py
from functools import wraps
from flask import request, g
from .models.audit_log import AuditLog, AuditActions

def audit_log(action: str, resource_type: str = None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 執行原始路由函式
            response = f(*args, **kwargs)

            # 從回應中獲取狀態碼和資料
            status_code = response.status_code
            try:
                response_data = response.get_json()
            except Exception:
                response_data = None

            # 判斷操作是否成功
            status = "success" if 200 <= status_code < 300 else "failed"

            # 獲取執行者 ID (actor_id)
            actor_id = g.get("user_id", None)

            # 對於成功的登入/註冊，執行者就是該用戶
            if not actor_id and status == "success" and action in [AuditActions.LOGIN, AuditActions.REGISTER]:
                if response_data and "user" in response_data:
                    actor_id = response_data.get("user", {}).get("id")

            # 獲取目標資源 ID (resource_id)
            resource_id = kwargs.get("user_id") or kwargs.get("id")
            if not resource_id and status == "success" and action == AuditActions.REGISTER:
                if response_data and "user" in response_data:
                    resource_id = response_data.get("user", {}).get("id")

            # 對於個人資料更新，資源就是用戶自己
            if action == AuditActions.USER_UPDATED and actor_id:
                resource_id = actor_id

            # 記錄日誌
            AuditLog.log_action(
                action=action,
                user_id=actor_id,  # 執行操作的用戶
                resource_type=resource_type,
                resource_id=resource_id,  # 被操作的資源
                details={
                    "request_args": request.args.to_dict(),
                    "request_json": request.get_json(silent=True),
                    "response_data": response_data,
                    "status_code": status_code,
                },
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status=status,
            )

            return response

        return decorated_function

    return decorator

