# MorningAI MVP (Seed)

This is a cleaned seed extracted from the legacy package.
- apps/web: Vite + React (shadcn/tailwind)
- apps/api: Flask API (replace SQLite with Postgres)
- infra: Dockerfiles and docker-compose
- .github/workflows: CI stub

## Local (Docker)
```
cd infra
docker compose up --build
```

API: http://localhost:8000  
Web: http://localhost:5173





# 🚀 MorningAI MVP – 開發環境配置

這份文件旨在提供 MorningAI MVP 專案的開發環境配置指南，確保所有開發者都能快速且一致地設定好開發環境。

## 1. Node.js / NVM

建議透過 [nvm (Node Version Manager)](https://github.com/nvm-sh/nvm) 管理 Node.js 版本，以確保專案使用正確的 Node.js 環境。

**Node.js 版本: 20.19.5**

### 安裝與使用 NVM

1.  **安裝 NVM** (如果尚未安裝)：

    ```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    ```

    安裝完成後，請重新啟動終端機或執行 `source ~/.bashrc` (或 `~/.zshrc`) 以載入 NVM。

2.  **安裝並使用指定版本的 Node.js**：

    ```bash
    nvm install 20
    nvm use 20
    ```

3.  **確認 Node.js 版本**：

    ```bash
    node -v  # 應顯示 v20.19.5
    ```

## 2. 必要套件版本

專案中已在 `devDependencies` 中固定了以下必要套件的版本，以確保開發環境的一致性：

*   **tailwindcss**: `3.4.17`
*   **postcss**: `8.5.6`
*   **autoprefixer**: `10.4.21`

### 重新安裝套件

如果遇到套件相關問題，可以透過以下步驟重新安裝所有套件：

```bash
rm -rf node_modules package-lock.json .next
npm install
```

## 3. PostCSS 設定

PostCSS 的設定檔位於專案根目錄下的 `postcss.config.cjs`。

**檔案：`postcss.config.cjs`**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

## 4. Tailwind 設定

Tailwind CSS 的設定檔位於專案根目錄下的 `tailwind.config.cjs`。

**檔案：`tailwind.config.cjs`**

```javascript
/** @type {import(\'tailwindcss\').Config} */
module.exports = {
  content: ["./src/app/**/*.{js,jsx,ts,tsx,mdx}"],
  theme: { extend: {} },
  plugins: [],
}
```

## 5. 全域樣式

全域樣式檔案 `globals.css` 引入了 Tailwind CSS 的基礎、組件和工具樣式。

**檔案：`src/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## 6. App Router 架構 (Next.js 14)

專案採用 Next.js 14 的 App Router 架構，以下是主要的檔案結構範例：

### `src/app/layout.jsx`

這是應用程式的根佈局檔案，用於定義 HTML 結構和引入全域樣式。

```javascript
import \'./globals.css\'

export default function RootLayout({ children }) {
  return (<html lang="en"><body>{children}</body></html>)
}
```

### `src/app/page.jsx`

這是應用程式的首頁組件，展示了 Tailwind CSS 是否正確配置。

```javascript
export default function Page() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-blue-600">Tailwind OK ✅</h1>
    </div>
  )
}
```

## 7. 啟動專案

按照以下步驟啟動開發伺服器並驗證配置：

1.  **啟動開發伺服器**：

    ```bash
    npm run dev -- -p 3001
    ```

2.  **開啟瀏覽器**：

    在瀏覽器中訪問 `http://127.0.0.1:3001`

3.  **驗證配置**：

    若您能看到頁面上顯示 **"Tailwind OK ✅"**，則代表開發環境配置正確。


