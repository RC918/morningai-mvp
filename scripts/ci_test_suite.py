#!/usr/bin/env python3
"""
CI/CD 測試套件 - 整合所有必要的測試
用於 GitHub Actions 中確保 CI/CD 流程的完整性
"""

import subprocess
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

class CITestSuite:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        }
        self.project_root = Path(__file__).parent.parent
        
    def run_test(self, test_name, command, working_dir=None):
        """運行單個測試並記錄結果"""
        print(f"\n🧪 運行測試: {test_name}")
        print(f"📋 命令: {' '.join(command) if isinstance(command, list) else command}")
        
        start_time = time.time()
        
        try:
            if working_dir:
                result = subprocess.run(
                    command,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 分鐘超時
                )
            else:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            self.results['tests'][test_name] = {
                'success': success,
                'duration': round(duration, 2),
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            if success:
                print(f"  ✅ 通過 ({duration:.2f}s)")
                self.results['summary']['passed'] += 1
            else:
                print(f"  ❌ 失敗 ({duration:.2f}s)")
                print(f"  錯誤: {result.stderr}")
                self.results['summary']['failed'] += 1
                
            self.results['summary']['total'] += 1
            
        except subprocess.TimeoutExpired:
            print(f"  ⏰ 超時 (>300s)")
            self.results['tests'][test_name] = {
                'success': False,
                'duration': 300,
                'stdout': '',
                'stderr': 'Test timed out after 300 seconds',
                'return_code': -1
            }
            self.results['summary']['failed'] += 1
            self.results['summary']['total'] += 1
            
        except Exception as e:
            print(f"  💥 異常: {str(e)}")
            self.results['tests'][test_name] = {
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': str(e),
                'return_code': -2
            }
            self.results['summary']['failed'] += 1
            self.results['summary']['total'] += 1
    
    def run_backend_tests(self):
        """運行後端測試"""
        print("\n🔧 後端測試套件")
        print("=" * 50)
        
        api_dir = self.project_root / "apps" / "api"
        
        # 1. 導入煙霧測試
        self.run_test(
            "import_smoke_test",
            [sys.executable, "../../scripts/import_smoke_test.py"],
            working_dir=api_dir
        )
        
        # 2. 單元測試 (健康檢查和 JWT 黑名單)
        self.run_test(
            "pytest_core",
            [sys.executable, "-m", "pytest", "src/tests/", "-v", "--tb=short"],
            working_dir=api_dir
        )
        
        # 3. 代碼風格檢查
        self.run_test(
            "flake8_lint",
            [sys.executable, "-m", "flake8", "src/", "--ignore=E402,E501,E302,W391,E117,W293"],
            working_dir=api_dir
        )
    
    def run_frontend_tests(self):
        """運行前端測試"""
        print("\n🌐 前端測試套件")
        print("=" * 50)
        
        web_dir = self.project_root / "apps" / "web"
        
        # 1. ESLint 檢查
        self.run_test(
            "eslint_check",
            ["npm", "run", "lint"],
            working_dir=web_dir
        )
        
        # 2. TypeScript 類型檢查
        self.run_test(
            "typescript_check",
            ["npm", "run", "typecheck"],
            working_dir=web_dir
        )
        
        # 3. 前端單元測試
        self.run_test(
            "vitest_unit",
            ["npm", "run", "test", "--run"],
            working_dir=web_dir
        )
    
    def run_integration_tests(self):
        """運行整合測試"""
        print("\n🔗 整合測試套件")
        print("=" * 50)
        
        # 1. E2E 煙霧測試
        self.run_test(
            "e2e_smoke_test",
            [sys.executable, "scripts/e2e_smoke_test.py"],
            working_dir=self.project_root
        )
        
        # 2. 環境變數檢查
        self.run_test(
            "env_check",
            ["node", "ops/env/scripts/check_env.mjs", "--app", "api"],
            working_dir=self.project_root
        )
        
        # 3. RLS 安全測試 (可選，可能需要資料庫連接)
        if os.getenv('RUN_SECURITY_TESTS', 'false').lower() == 'true':
            self.run_test(
                "rls_security_test",
                [sys.executable, "scripts/rls_security_test.py"],
                working_dir=self.project_root
            )
    
    def generate_report(self):
        """生成測試報告"""
        # 計算成功率
        if self.results['summary']['total'] > 0:
            self.results['summary']['success_rate'] = round(
                (self.results['summary']['passed'] / self.results['summary']['total']) * 100, 2
            )
        
        # 保存 JSON 報告
        report_file = self.project_root / "ci_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("📊 CI/CD 測試套件結果摘要")
        print("=" * 60)
        print(f"總測試數: {self.results['summary']['total']}")
        print(f"通過: {self.results['summary']['passed']}")
        print(f"失敗: {self.results['summary']['failed']}")
        print(f"成功率: {self.results['summary']['success_rate']}%")
        
        # 列出失敗的測試
        failed_tests = [name for name, result in self.results['tests'].items() if not result['success']]
        if failed_tests:
            print(f"\n❌ 失敗的測試:")
            for test in failed_tests:
                print(f"  - {test}")
        
        print(f"\n📄 詳細報告已保存至: {report_file}")
        
        # GitHub Actions 輸出
        if os.getenv('GITHUB_ACTIONS'):
            print(f"\n::set-output name=success_rate::{self.results['summary']['success_rate']}")
            print(f"::set-output name=total_tests::{self.results['summary']['total']}")
            print(f"::set-output name=passed_tests::{self.results['summary']['passed']}")
            print(f"::set-output name=failed_tests::{self.results['summary']['failed']}")
        
        return self.results['summary']['failed'] == 0

def main():
    """主函數"""
    print("🚀 CI/CD 測試套件")
    print("=" * 60)
    print(f"📅 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    suite = CITestSuite()
    
    # 檢查是否在正確的目錄
    if not (suite.project_root / "apps").exists():
        print("❌ 錯誤: 請在專案根目錄執行此腳本")
        sys.exit(1)
    
    try:
        # 運行測試套件
        suite.run_backend_tests()
        suite.run_frontend_tests()
        suite.run_integration_tests()
        
        # 生成報告
        success = suite.generate_report()
        
        if success:
            print("\n🎉 所有測試通過！")
            sys.exit(0)
        else:
            print("\n💥 部分測試失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 測試套件執行異常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
