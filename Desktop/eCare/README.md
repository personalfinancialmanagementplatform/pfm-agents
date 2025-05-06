## 環境安裝

### eCare 專案開發指南（Next.js 前後端分離架構）

本專案為 eCare 系統，採用 Next.js 開發，並以前後端分離架構實作：

- `frontend/`：前端使用者介面（Next.js）
- `backend/`：後端 API 功能與邏輯（Next.js API Routes）

---

### 專案目錄結構
```
.
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── login/
│   │   ├── dashboard/
│   │   └── alerts/
│   ├── components/
│   │   ├── PatientCard.tsx
│   │   └── VitalChart.tsx
│   ├── lib/
│   │   └── api.ts               # 封裝呼叫 backend API 的函式
│   ├── types/
│   │   ├── user.ts
│   │   └── patient.ts
│   ├── public/
│   ├── styles/
│   │   └── globals.css
│   ├── .env.local               # NEXT_PUBLIC_API_BASE_URL=http://localhost:3001
│   ├── next.config.js
│   └── package.json
├── app/
│   ├── pages/api
│   │   ├── user
│   │   │     ├── signup.ts
│   │   │     ├── logout.ts
│   │   │     ├── login.ts
│   │   │     └── getinfo.ts
│   │   ├── patient
│   │   │     ├── create.ts
│   │   │     ├── delete.ts
│   │   │     ├── get.ts
│   │   │     ├── getAll.ts
│   │   │     ├── read.ts
│   │   │     └── update.ts
│   │   ├── vitalSign
│   │   │     ├── create.ts
│   │   │     ├── delete.ts
│   │   │     ├── get.ts
│   │   │     ├── getAll.ts
│   │   │     └── update.ts
│   │   ├── alert
│   │   │     ├── create.ts
│   │   │     ├── getUnread.ts
│   │   │     └── read.ts
│   │   ├── healthTrend
│   │   │     └── table.ts
│   │   └──health.ts
│   ├── favicon.ico
│   ├── globals.css
│   ├── layout.tsx
│   ├── lib
│   │   └──health_db.sql
│   │   └──db.ts, etc
│   ├── page.tsx
│   └── signup
│       └── page.tsx
├── bun.lock
├── eslint.config.mjs
├── next-env.d.ts
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── public
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── README.md
└── tsconfig.json
```
---

### Step 1：安裝 Node.js（建議版本 ≥ 18.17）

如果尚未安裝，請先安裝 [Node.js](https://nodejs.org/)，或使用 nvm 管理版本。

### Step 2：安裝前端/後端dependencies

# 前端安裝

cd frontend/
npm install

# 回到專案根目錄後，安裝後端

cd ../backend/
npm install

### Step 3：啟動後端伺服器（backend）

cd backend/
npm run dev

預設port：http://localhost:3001

### Step 4：啟動前端伺服器（frontend）

cd frontend/
npm run dev

預設port：http://localhost:3000

---

## NEXT.js介紹

### API Routes

Next.js 的 API Routes 採用了 **file-based routing**，也就是**每個檔案代表一個 route**，而檔案名稱（file name）會變成該 API 的 **path name（路徑名稱）**，不需要手動寫 router 設定，不需要東寫一個 route、南寫一個 path，只要在正確的地方放檔案，Next.js 就會幫你開好路！

Next.js 會把 pages/api/ 目錄下的所有檔案當作 API route：

- pages/api/index.js → 對應到 `/` API route
- pages/api/user.js → 對應到 /user API route
- pages/api/vital.js → 對應到 /vital API route

### 特性

API Routes 裡的所有程式碼**只會在伺服器端執行-SSR (Server Side Rendering)**，不會被打包進瀏覽器端的 JavaScript 中：

- 不會增加前端 bundle size
- 不影響網頁下載速度
- 可安全操作後端資源（如資料庫），安全性高！

### 建立 API Route 的方式

每個 pages/api/ 資料夾下的檔案，都需要 export default 一個函式，作為 API 的 **request handler（處理請求的函式）**。

這個 handler 函式會接收兩個參數：

```
js
export default function handler(req, res) {
  // req: request 物件（http.IncomingMessage）
  // res: response 物件（http.ServerResponse）
}

```

### pkg to install

npm
```
install npm
```
@prisma/client
```
npm install @prisma/client
```
bcrypt
```
npm i --save-dev @types/bcrypt
```
ts-node
```
npm install --save-dev ts-node typescript
```
express
```
npm install --save-dev @types/express
```

mySQL2
```
npm install mysql2
```
