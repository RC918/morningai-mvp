#!/usr/bin/env python3
"""
RLS/權限測試集 - 加入「越權嘗試」與「黑名單 token」自動測試
"""

import requests
import json
import sys
import os
from datetime import datetime

class SecurityTestSuite:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url.rstrip('/')
        self.test_results = []
        self.admin_token = None
        self.user_token = None
        self.blacklisted_token = None
        
    def log_test(self, test_name, success, details, severity="INFO"):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method, endpoint, headers=None, json_data=None, expected_status=None):
        """發送 HTTP 請求"""
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                json=json_data,
                timeout=10
            )
            
            result = {
                "status_code": response.status_code,
                "url": url,
                "method": method
            }
            
            try:
                result["json"] = response.json()
            except:
                result["text"] = response.text[:200]
            
            if expected_status and response.status_code != expected_status:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
                
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "url": url,
                "method": method
            }
    
    def setup_test_users(self):
        """設置測試用戶"""
        print("🔧 設置測試用戶...")
        
        # 嘗試登入管理員
        admin_login = self.make_request(
            "POST", 
            "/api/login",
            json_data={
                "email": "admin@morningai.com",
                "password": "admin123"
            }
        )
        
        if admin_login.get("status_code") == 200 and "json" in admin_login:
            self.admin_token = admin_login["json"].get("access_token")
            self.log_test("管理員登入", True, "成功獲取管理員 token")
        else:
            self.log_test("管理員登入", False, f"失敗: {admin_login}", "ERROR")
            
        # 嘗試創建普通用戶（如果不存在）
        user_register = self.make_request(
            "POST",
            "/api/register", 
            json_data={
                "email": "testuser@example.com",
                "password": "testpass123",
                "name": "Test User"
            }
        )
        
        # 如果註冊失敗，可能用戶已存在，直接嘗試登入
        if user_register.get("status_code") not in [200, 201]:
            self.log_test("用戶註冊", False, f"註冊失敗或用戶已存在: {user_register.get('status_code')}", "INFO")
        else:
            self.log_test("用戶註冊", True, "成功註冊測試用戶")
        
        # 登入普通用戶
        user_login = self.make_request(
            "POST",
            "/api/login",
            json_data={
                "email": "testuser@example.com", 
                "password": "testpass123"
            }
        )
        
        if user_login.get("status_code") == 200 and "json" in user_login:
            self.user_token = user_login["json"].get("access_token")
            self.log_test("普通用戶登入", True, "成功獲取用戶 token")
        else:
            self.log_test("普通用戶登入", False, f"失敗: {user_login}", "ERROR")
    
    def test_privilege_escalation(self):
        """測試越權嘗試"""
        print("\n🔒 測試越權嘗試...")
        
        if not self.user_token:
            self.log_test("越權測試", False, "無法獲取普通用戶 token", "ERROR")
            return
            
        # 測試 1: 普通用戶嘗試訪問管理員端點
        admin_users_response = self.make_request(
            "GET",
            "/api/admin/users",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        success = admin_users_response.get("status_code") in [401, 403]
        self.log_test(
            "普通用戶訪問管理員端點",
            success,
            f"狀態碼: {admin_users_response.get('status_code')} (應為 401/403)",
            "HIGH" if not success else "INFO"
        )
        
        # 測試 2: 普通用戶嘗試修改其他用戶資料
        if self.admin_token:
            # 先獲取管理員用戶 ID
            profile_response = self.make_request(
                "GET",
                "/api/profile",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            
            if profile_response.get("status_code") == 200:
                admin_user_id = profile_response.get("json", {}).get("id")
                
                if admin_user_id:
                    # 普通用戶嘗試修改管理員資料
                    modify_response = self.make_request(
                        "PUT",
                        f"/api/admin/users/{admin_user_id}/role",
                        headers={"Authorization": f"Bearer {self.user_token}"},
                        json_data={"role": "user"}
                    )
                    
                    success = modify_response.get("status_code") in [401, 403]
                    self.log_test(
                        "普通用戶修改管理員資料",
                        success,
                        f"狀態碼: {modify_response.get('status_code')} (應為 401/403)",
                        "HIGH" if not success else "INFO"
                    )
        
        # 測試 3: 普通用戶嘗試訪問審計日誌
        audit_response = self.make_request(
            "GET",
            "/api/admin/audit-logs",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        success = audit_response.get("status_code") in [401, 403]
        self.log_test(
            "普通用戶訪問審計日誌",
            success,
            f"狀態碼: {audit_response.get('status_code')} (應為 401/403)",
            "HIGH" if not success else "INFO"
        )
    
    def test_blacklisted_token(self):
        """測試黑名單 token"""
        print("\n🚫 測試黑名單 token...")
        
        if not self.user_token:
            self.log_test("黑名單 token 測試", False, "無法獲取用戶 token", "ERROR")
            return
            
        # 先測試 token 是否有效
        profile_before = self.make_request(
            "GET",
            "/api/profile",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        if profile_before.get("status_code") != 200:
            self.log_test("Token 有效性檢查", False, "Token 無效，無法進行黑名單測試", "ERROR")
            return
            
        self.log_test("Token 有效性檢查", True, "Token 在登出前有效")
        
        # 執行登出操作（將 token 加入黑名單）
        logout_response = self.make_request(
            "POST",
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        if logout_response.get("status_code") == 200:
            self.log_test("登出操作", True, "成功執行登出")
            self.blacklisted_token = self.user_token
        else:
            self.log_test("登出操作", False, f"登出失敗: {logout_response}", "ERROR")
            return
        
        # 測試黑名單 token 是否被拒絕
        profile_after = self.make_request(
            "GET",
            "/api/profile", 
            headers={"Authorization": f"Bearer {self.blacklisted_token}"}
        )
        
        success = profile_after.get("status_code") == 401
        expected_message = "Token has been revoked"
        actual_message = profile_after.get("json", {}).get("message", "")
        
        self.log_test(
            "黑名單 Token 拒絕",
            success and expected_message in actual_message,
            f"狀態碼: {profile_after.get('status_code')}, 訊息: {actual_message}",
            "HIGH" if not success else "INFO"
        )
        
        # 測試黑名單 token 訪問其他端點
        endpoints_to_test = [
            "/api/admin/users",
            "/api/auth/2fa/status", 
            "/api/audit-logs/my"
        ]
        
        for endpoint in endpoints_to_test:
            response = self.make_request(
                "GET",
                endpoint,
                headers={"Authorization": f"Bearer {self.blacklisted_token}"}
            )
            
            success = response.get("status_code") == 401
            self.log_test(
                f"黑名單 Token 訪問 {endpoint}",
                success,
                f"狀態碼: {response.get('status_code')} (應為 401)",
                "MEDIUM" if not success else "INFO"
            )
    
    def test_rls_policies(self):
        """測試 RLS 政策"""
        print("\n🛡️ 測試 RLS 政策...")
        
        if not self.user_token:
            self.log_test("RLS 政策測試", False, "無法獲取用戶 token", "ERROR")
            return
            
        # 測試用戶只能查看自己的審計日誌
        my_audit_logs = self.make_request(
            "GET",
            "/api/audit-logs/my",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        success = my_audit_logs.get("status_code") in [200, 404]  # 200 有日誌，404 無日誌都是正常的
        self.log_test(
            "用戶查看自己的審計日誌",
            success,
            f"狀態碼: {my_audit_logs.get('status_code')}",
            "MEDIUM" if not success else "INFO"
        )
        
        # 測試用戶無法查看所有審計日誌
        all_audit_logs = self.make_request(
            "GET", 
            "/api/admin/audit-logs",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        success = all_audit_logs.get("status_code") in [401, 403]
        self.log_test(
            "用戶無法查看所有審計日誌",
            success,
            f"狀態碼: {all_audit_logs.get('status_code')} (應為 401/403)",
            "HIGH" if not success else "INFO"
        )
    
    def test_input_validation(self):
        """測試輸入驗證"""
        print("\n🔍 測試輸入驗證...")
        
        # 測試 SQL 注入嘗試
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; --",
            "1' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_injection_payloads:
            login_response = self.make_request(
                "POST",
                "/api/login",
                json_data={
                    "email": payload,
                    "password": "test"
                }
            )
            
            # 應該返回 400 (驗證錯誤) 或 401 (認證失敗)，而不是 500 (伺服器錯誤)
            success = login_response.get("status_code") in [400, 401, 422]
            self.log_test(
                f"SQL 注入防護 ({payload[:20]}...)",
                success,
                f"狀態碼: {login_response.get('status_code')}",
                "HIGH" if not success else "INFO"
            )
    
    def generate_report(self):
        """生成測試報告"""
        print("\n📊 生成安全測試報告...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - passed_tests
        
        # 按嚴重程度分類失敗的測試
        high_severity_failures = [test for test in self.test_results 
                                if not test["success"] and test["severity"] == "HIGH"]
        medium_severity_failures = [test for test in self.test_results 
                                  if not test["success"] and test["severity"] == "MEDIUM"]
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "high_severity_failures": len(high_severity_failures),
                "medium_severity_failures": len(medium_severity_failures)
            },
            "test_results": self.test_results,
            "high_severity_failures": high_severity_failures,
            "medium_severity_failures": medium_severity_failures
        }
        
        # 保存報告
        with open("rls_security_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📈 測試成功率: {report['summary']['success_rate']:.1f}%")
        print(f"🔴 高嚴重度失敗: {len(high_severity_failures)}")
        print(f"🟡 中嚴重度失敗: {len(medium_severity_failures)}")
        
        if high_severity_failures:
            print("\n🚨 高嚴重度安全問題:")
            for failure in high_severity_failures:
                print(f"  - {failure['test_name']}: {failure['details']}")
        
        return report
    
    def run_all_tests(self):
        """執行所有安全測試"""
        print("🔒 RLS/權限安全測試套件")
        print("=" * 50)
        
        self.setup_test_users()
        self.test_privilege_escalation()
        self.test_blacklisted_token()
        self.test_rls_policies()
        self.test_input_validation()
        
        report = self.generate_report()
        
        # 如果有高嚴重度失敗，返回錯誤碼
        if report["summary"]["high_severity_failures"] > 0:
            print("\n❌ 發現高嚴重度安全問題，測試失敗")
            return 1
        elif report["summary"]["failed_tests"] > 0:
            print("\n⚠️ 發現安全問題，但非高嚴重度")
            return 0
        else:
            print("\n✅ 所有安全測試通過")
            return 0

def main():
    """主函數"""
    api_url = os.getenv("API_URL", "https://morningai-mvp.onrender.com")
    
    test_suite = SecurityTestSuite(api_url)
    exit_code = test_suite.run_all_tests()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
