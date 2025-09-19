# 代碼品質指南

## 概述

本文檔描述了 MorningAI MVP 專案的代碼品質標準、工具配置和最佳實踐。

## 代碼品質工具

### Python (API)

#### 1. Black - 代碼格式化
- **用途**: 自動格式化 Python 代碼
- **配置**: `apps/api/pyproject.toml`
- **執行**: `black src/`
- **檢查**: `black --check src/`

#### 2. isort - 導入排序
- **用途**: 自動排序和組織 Python 導入語句
- **配置**: `apps/api/pyproject.toml`
- **執行**: `isort src/`
- **檢查**: `isort --check-only src/`

#### 3. Flake8 - 代碼檢查
- **用途**: Python 代碼風格和錯誤檢查
- **配置**: `apps/api/pyproject.toml`
- **執行**: `flake8 src/`

#### 4. Bandit - 安全檢查
- **用途**: Python 代碼安全漏洞檢測
- **配置**: `apps/api/pyproject.toml`
- **執行**: `bandit -r src/`

#### 5. MyPy - 類型檢查
- **用途**: Python 靜態類型檢查
- **配置**: `apps/api/pyproject.toml`
- **執行**: `mypy src/`

### JavaScript/TypeScript (Web)

#### 1. ESLint - 代碼檢查
- **用途**: JavaScript/TypeScript 代碼風格和錯誤檢查
- **配置**: `apps/web/.eslintrc.json`
- **執行**: `npm run lint`

#### 2. Prettier - 代碼格式化
- **用途**: 自動格式化 JavaScript/TypeScript 代碼
- **配置**: `apps/web/.prettierrc`
- **執行**: `npm run format`

#### 3. TypeScript - 類型檢查
- **用途**: TypeScript 靜態類型檢查
- **配置**: `apps/web/tsconfig.json`
- **執行**: `npm run typecheck`

### 通用工具

#### 1. Pre-commit Hooks
- **用途**: Git 提交前自動執行代碼品質檢查
- **配置**: `.pre-commit-config.yaml`
- **安裝**: `pre-commit install`
- **執行**: `pre-commit run --all-files`

#### 2. detect-secrets - 秘密檢測
- **用途**: 檢測代碼中的敏感資訊
- **配置**: `.secrets.baseline`
- **執行**: `detect-secrets scan`

## 代碼品質標準

### Python 代碼標準

1. **格式化**
   - 使用 Black 進行代碼格式化
   - 行長度限制為 88 字符
   - 使用雙引號作為字符串分隔符

2. **導入組織**
   - 使用 isort 進行導入排序
   - 導入順序：標準庫 → 第三方庫 → 本地模組
   - 每組導入之間用空行分隔

3. **代碼風格**
   - 遵循 PEP 8 標準
   - 使用有意義的變數和函數名稱
   - 添加適當的文檔字符串

4. **類型註解**
   - 為所有公共函數添加類型註解
   - 使用 MyPy 進行類型檢查
   - 避免使用 `Any` 類型

5. **安全性**
   - 避免使用不安全的函數
   - 不在代碼中硬編碼敏感資訊
   - 使用參數化查詢防止 SQL 注入

### JavaScript/TypeScript 代碼標準

1. **格式化**
   - 使用 Prettier 進行代碼格式化
   - 使用 2 空格縮進
   - 使用單引號作為字符串分隔符

2. **代碼風格**
   - 遵循 Airbnb JavaScript 風格指南
   - 使用 ESLint 進行代碼檢查
   - 使用有意義的變數和函數名稱

3. **TypeScript**
   - 啟用嚴格模式
   - 為所有函數添加類型註解
   - 避免使用 `any` 類型

4. **React 最佳實踐**
   - 使用函數組件和 Hooks
   - 遵循 React Hooks 規則
   - 使用 TypeScript 定義組件 props

## 使用指南

### 本地開發

1. **安裝開發依賴**
   ```bash
   # Python
   cd apps/api
   pip install -r requirements-dev.txt
   
   # JavaScript
   cd apps/web
   npm install
   ```

2. **安裝 Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

3. **運行代碼品質檢查**
   ```bash
   # 使用自動化腳本
   ./scripts/code-quality.sh
   
   # 或手動運行各個工具
   cd apps/api
   black src/
   isort src/
   flake8 src/
   bandit -r src/
   mypy src/
   
   cd ../web
   npm run lint
   npm run typecheck
   npm run format
   ```

### CI/CD 集成

代碼品質檢查已集成到 GitHub Actions 工作流程中：

- **ci-check.yml**: 基本的代碼品質檢查
- **security-check.yml**: 安全相關檢查
- **pre-commit**: 每次提交前自動執行

### 配置檔案

| 工具 | 配置檔案 | 位置 |
|------|----------|------|
| Black | pyproject.toml | apps/api/ |
| isort | pyproject.toml | apps/api/ |
| Flake8 | pyproject.toml | apps/api/ |
| Bandit | pyproject.toml | apps/api/ |
| MyPy | pyproject.toml | apps/api/ |
| ESLint | .eslintrc.json | apps/web/ |
| Prettier | .prettierrc | apps/web/ |
| TypeScript | tsconfig.json | apps/web/ |
| Pre-commit | .pre-commit-config.yaml | 根目錄 |
| Secrets | .secrets.baseline | 根目錄 |

## 最佳實踐

### 1. 提交前檢查
- 始終在提交前運行代碼品質檢查
- 使用 pre-commit hooks 自動化此過程
- 修復所有警告和錯誤

### 2. 代碼審查
- 在 Pull Request 中包含代碼品質檢查結果
- 確保所有 CI 檢查通過
- 審查者應關注代碼品質和安全性

### 3. 持續改進
- 定期更新代碼品質工具
- 根據專案需求調整配置
- 學習和採用新的最佳實踐

### 4. 文檔維護
- 保持代碼註釋和文檔字符串更新
- 記錄重要的設計決策
- 更新 README 和其他文檔

## 忽略規則

### 何時忽略規則
- 第三方庫兼容性問題
- 特殊的業務邏輯需求
- 性能優化需要

### 如何忽略規則
```python
# Python - 使用 # noqa 註釋
password = "hardcoded_password"  # noqa: S105 - 這是測試用的假密碼

# 或使用 # type: ignore 忽略類型檢查
result = some_untyped_function()  # type: ignore
```

```javascript
// JavaScript - 使用 eslint-disable 註釋
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = await fetchData();
```

### 忽略規則的原則
- 必須添加說明註釋
- 儘量使用行級忽略而非檔案級
- 定期檢查和清理不必要的忽略

## 故障排除

### 常見問題

1. **Black 和 Flake8 衝突**
   - 確保 Flake8 配置忽略 E203 和 W503
   - 使用相同的行長度設置

2. **Import 順序問題**
   - 確保 isort 和 Black 配置兼容
   - 使用 `profile = "black"` 設置

3. **TypeScript 類型錯誤**
   - 安裝相應的類型定義包
   - 使用 `@types/` 包提供類型

4. **Pre-commit Hook 失敗**
   - 檢查工具是否正確安裝
   - 確保配置檔案語法正確

### 獲取幫助

- 查看工具官方文檔
- 檢查 GitHub Issues
- 諮詢團隊成員
- 參考專案的 CI 日誌

## 版本歷史

- **v1.0** (2025-09-19): 初始代碼品質配置
  - 設置 Python 代碼品質工具
  - 配置 JavaScript/TypeScript 檢查
  - 實施 Pre-commit Hooks
  - 創建自動化檢查腳本
