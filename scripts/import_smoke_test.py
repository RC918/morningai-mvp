#!/usr/bin/env python3
"""
Import Smoke Test - 檢查所有路由模組的導入狀態
對 src.routes.* 做 import 檢查，提早抓缺失匯入
"""

import sys
import os
import importlib
import traceback
from pathlib import Path

def find_route_modules(base_path):
    """找到所有路由模組"""
    routes_path = Path(base_path) / "src" / "routes"
    if not routes_path.exists():
        print(f"❌ Routes directory not found: {routes_path}")
        return []
    
    modules = []
    for py_file in routes_path.glob("*.py"):
        if py_file.name != "__init__.py":
            module_name = f"src.routes.{py_file.stem}"
            modules.append(module_name)
    
    return modules

def test_import(module_name):
    """測試單個模組的導入"""
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """主函數"""
    print("🔍 Import Smoke Test - 檢查路由模組導入")
    print("=" * 50)
    
    # 檢查是否在正確的目錄
    if not os.path.exists("src/routes"):
        print("❌ 錯誤：未找到 src/routes 目錄")
        print("請在 apps/api 目錄下執行此腳本")
        sys.exit(1)
    
    # 添加當前目錄到 Python 路徑
    sys.path.insert(0, os.getcwd())
    
    # 找到所有路由模組
    modules = find_route_modules(".")
    if not modules:
        print("❌ 未找到任何路由模組")
        sys.exit(1)
    
    print(f"📦 找到 {len(modules)} 個路由模組:")
    for module in modules:
        print(f"  - {module}")
    print()
    
    # 測試每個模組的導入
    failed_imports = []
    successful_imports = []
    
    for module in modules:
        print(f"🧪 測試導入: {module}")
        success, error = test_import(module)
        
        if success:
            print(f"  ✅ 成功")
            successful_imports.append(module)
        else:
            print(f"  ❌ 失敗: {error}")
            failed_imports.append((module, error))
    
    print()
    print("📊 測試結果:")
    print(f"  ✅ 成功: {len(successful_imports)}")
    print(f"  ❌ 失敗: {len(failed_imports)}")
    
    if failed_imports:
        print()
        print("❌ 失敗的模組詳情:")
        for module, error in failed_imports:
            print(f"  {module}: {error}")
        
        print()
        print("🔧 建議修復:")
        print("  1. 檢查缺失的依賴套件")
        print("  2. 檢查模組內的語法錯誤")
        print("  3. 檢查循環導入問題")
        print("  4. 檢查環境變數配置")
        
        sys.exit(1)
    
    print()
    print("🎉 所有路由模組導入測試通過！")
    return 0

if __name__ == "__main__":
    main()
