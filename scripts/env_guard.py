#!/usr/bin/env python3
"""
Environment Guard - 環境變數檢查守衛
以 ops/env/*.json 校驗必要鍵（缺鍵即紅）
"""

import json
import os
import sys
from pathlib import Path

def load_env_config(config_path):
    """載入環境變數配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式錯誤: {config_path}")
        print(f"   錯誤: {e}")
        return None

def check_env_vars(config, env_name):
    """檢查環境變數"""
    print(f"🔍 檢查 {env_name} 環境變數")
    print(f"📝 描述: {config.get('description', 'N/A')}")
    print()
    
    required_vars = config.get('required', [])
    optional_vars = config.get('optional', [])
    
    missing_required = []
    missing_optional = []
    present_vars = []
    
    # 檢查必要變數
    for var in required_vars:
        if os.getenv(var):
            present_vars.append(var)
            print(f"  ✅ {var}: 已設定")
        else:
            missing_required.append(var)
            print(f"  ❌ {var}: 缺失 (必要)")
    
    # 檢查可選變數
    for var in optional_vars:
        if os.getenv(var):
            present_vars.append(var)
            print(f"  ✅ {var}: 已設定 (可選)")
        else:
            missing_optional.append(var)
            print(f"  ⚠️  {var}: 缺失 (可選)")
    
    print()
    print(f"📊 統計:")
    print(f"  ✅ 已設定: {len(present_vars)}")
    print(f"  ❌ 缺失必要: {len(missing_required)}")
    print(f"  ⚠️  缺失可選: {len(missing_optional)}")
    
    return missing_required, missing_optional

def main():
    """主函數"""
    print("🛡️  Environment Guard - 環境變數檢查")
    print("=" * 50)
    
    # 檢查 ops/env 目錄
    ops_env_path = Path("ops/env")
    if not ops_env_path.exists():
        print(f"❌ 配置目錄不存在: {ops_env_path}")
        print("請確保在專案根目錄執行此腳本")
        sys.exit(1)
    
    # 找到所有配置文件
    config_files = list(ops_env_path.glob("*.json"))
    if not config_files:
        print(f"❌ 未找到任何配置文件在: {ops_env_path}")
        sys.exit(1)
    
    print(f"📁 找到 {len(config_files)} 個配置文件:")
    for config_file in config_files:
        print(f"  - {config_file.name}")
    print()
    
    # 檢查每個配置
    total_missing_required = []
    all_results = {}
    
    for config_file in config_files:
        env_name = config_file.stem
        config = load_env_config(config_file)
        
        if config is None:
            continue
        
        missing_required, missing_optional = check_env_vars(config, env_name)
        total_missing_required.extend(missing_required)
        
        all_results[env_name] = {
            'missing_required': missing_required,
            'missing_optional': missing_optional
        }
        
        print("-" * 30)
        print()
    
    # 總結報告
    print("🎯 總結報告:")
    print("=" * 30)
    
    if total_missing_required:
        print(f"❌ 總共缺失 {len(total_missing_required)} 個必要環境變數:")
        for var in total_missing_required:
            print(f"  - {var}")
        
        print()
        print("🔧 修復建議:")
        print("  1. 檢查 .env 文件是否存在")
        print("  2. 檢查部署平台的環境變數設定")
        print("  3. 參考 .env.example 文件")
        print("  4. 確認敏感變數已在 CI/CD 中設定")
        
        # 輸出 GitHub Actions 格式
        print()
        print("📋 GitHub Actions 輸出:")
        print(f"missing-vars={','.join(total_missing_required)}")
        
        sys.exit(1)
    else:
        print("✅ 所有必要環境變數都已設定！")
        
        # 統計可選變數
        total_missing_optional = []
        for result in all_results.values():
            total_missing_optional.extend(result['missing_optional'])
        
        if total_missing_optional:
            print(f"⚠️  {len(total_missing_optional)} 個可選環境變數未設定:")
            for var in total_missing_optional:
                print(f"  - {var}")
        
        print()
        print("📋 GitHub Actions 輸出:")
        print("missing-vars=None")
        
        return 0

if __name__ == "__main__":
    main()
