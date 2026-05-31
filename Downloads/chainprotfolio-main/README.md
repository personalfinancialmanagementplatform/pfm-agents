# Student Experience Badge Platform

本專案是一個基於區塊鏈的學生經歷與證明驗證平台。
平台允許學生自行上傳經歷，並由可信任的發證單位進行驗證。每一筆經歷都會對應一個鏈上 Badge NFT，並透過 `certHash` 確保資料未被竄改。

---

## 一、專案角色說明

### A：Smart Contract / Blockchain

負責撰寫與部署 `BadgeNFT.sol` 智慧合約。

主要功能：

* 發證單位白名單管理
* 學生自行上傳經歷
* 發證單位直接發證
* 發證單位驗證學生經歷
* 拒絕驗證
* 撤銷已驗證經歷
* 查詢學生所有經歷
* 查詢單一經歷詳細資料

---

### B：Issuer Web 發證單位端

負責學校、主辦方、社團或工作坊單位使用的後台。

主要功能：

* 發證單位連接 MetaMask
* 直接發行已驗證經歷
* 查看學生提交的經歷
* 驗證學生經歷
* 拒絕學生經歷
* 撤銷已驗證經歷

---

### C：Student Web 學生能力護照

負責學生端個人儀表板。

主要功能：

* 學生連接 MetaMask
* 學生自行上傳經歷
* 查看自己的所有經歷
* 顯示經歷狀態：Pending、Verified、Rejected、Revoked
* 產生 QR Code，讓他人驗證經歷

---

### D：Verifier Web 驗證者端

負責第三方驗證頁面。

主要功能：

* 不需要連接 MetaMask
* 根據 tokenId 查詢鏈上經歷資料
* 重新計算 hash
* 比對前端資料與鏈上 `certHash`
* 檢查狀態是否為 Verified
* 檢查發證單位是否為白名單地址
* 顯示驗證結果

---

## 二、技術使用

* Solidity
* Foundry
* OpenZeppelin ERC721
* Anvil
* Sepolia Testnet
* MetaMask
* ethers.js

---

## 三、安裝與編譯

### 1. Clone 專案

```bash
git clone <REPOSITORY_URL>
cd badge-platform
```

---

### 2. 安裝 Foundry dependencies

如果 `lib/openzeppelin-contracts` 不存在，請執行：

```bash
forge install OpenZeppelin/openzeppelin-contracts --no-commit
```

---

### 3. 編譯合約

```bash
forge build
```

如果看到：

```text
Compiler run successful
```

或：

```text
No files changed, compilation skipped
```

代表編譯成功。

---

## 四、本地 Anvil 測試流程

主要 A 測試智慧合約用。

---

### 1. 開啟 Anvil

開一個新的 terminal：

```bash
anvil
```

Anvil 預設帳號角色建議如下：

```text
Account 0：平台管理者 / owner / 部署者
Account 1：發證單位 issuer
Account 2：學生 student
```

---

### 2. 部署到 Anvil

```bash
forge create src/BadgeNFT.sol:BadgeNFT --rpc-url http://127.0.0.1:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 --broadcast
```

成功後會出現：

```text
Deployed to: 0x...
```

請將這個地址記下來，後面稱為：

```text
ANVIL_CONTRACT_ADDRESS
```

---

### 3. 加入發證單位白名單

將 Account 1 加入白名單：

```bash
cast send <ANVIL_CONTRACT_ADDRESS> "approveIssuer(address)" 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 --rpc-url http://127.0.0.1:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

檢查是否成功：

```bash
cast call <ANVIL_CONTRACT_ADDRESS> "approvedIssuers(address)(bool)" 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 --rpc-url http://127.0.0.1:8545
```

如果回傳：

```text
true
```

代表 Account 1 已經是可信發證單位。

---

## 五、Hash 格式規則

B、C、D 必須使用完全一樣的格式產生 `certHash`。

固定格式：

```text
studentName|studentWallet|eventName|awardTitle|issueDate
```

範例：

```text
張小明|0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC|AI黑客松|第一名|2026-05-27
```

在前端可以使用：

```javascript
import { ethers } from "ethers";

export function generateCertHash(
  studentName,
  studentWallet,
  eventName,
  awardTitle,
  issueDate
) {
  const rawText = `${studentName}|${studentWallet}|${eventName}|${awardTitle}|${issueDate}`;
  const certHash = ethers.keccak256(ethers.toUtf8Bytes(rawText));

  return {
    rawText,
    certHash
  };
}
```

注意：
只要空格、順序、符號、日期格式不同，算出來的 hash 就會不同。

---

## 六、學生自行上傳經歷

學生端 C 會使用此功能。

### 合約函式

```solidity
submitExperience(bytes32 certHash, string category, string experienceType)
```

### cast 測試範例

先產生 certHash：

```bash
cast keccak "張小明|0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC|AI黑客松|第一名|2026-05-27"
```

用 Account 2 上傳經歷：

```bash
cast send <ANVIL_CONTRACT_ADDRESS> "submitExperience(bytes32,string,string)" <CERT_HASH> "競賽獲獎" "AI黑客松" --rpc-url http://127.0.0.1:8545 --private-key 0x5de4111a56d6e7942fdaeef8f93ea3678280094ecece855267fbfca0c5da2a
```

成功後，該筆經歷狀態會是：

```text
Pending
```

---

## 七、查詢學生所有經歷

C 學生端會使用此功能。

### 合約函式

```solidity
getStudentExperiences(address student)
```

### cast 測試範例

```bash
cast call <ANVIL_CONTRACT_ADDRESS> "getStudentExperiences(address)(uint256[])" 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC --rpc-url http://127.0.0.1:8545
```

範例回傳：

```text
[0]
```

代表該學生有一筆 Token ID 為 `0` 的經歷。

---

## 八、查詢單一經歷詳細資料

B、C、D 都可能會使用此功能。

### 合約函式

```solidity
getExperience(uint256 tokenId)
```

### cast 測試範例

```bash
cast call <ANVIL_CONTRACT_ADDRESS> "getExperience(uint256)(bytes32,address,address,string,string,uint8,uint256,uint256)" 0 --rpc-url http://127.0.0.1:8545
```

回傳欄位順序：

```text
certHash
student
issuer
category
experienceType
status
submittedAt
verifiedAt
```

---

## 九、經歷狀態代碼

```text
0 = Unverified
1 = Pending
2 = Verified
3 = Rejected
4 = Revoked
```

前端可以這樣轉換：

```javascript
function statusText(status) {
  const statusMap = [
    "Unverified",
    "Pending",
    "Verified",
    "Rejected",
    "Revoked"
  ];

  return statusMap[Number(status)];
}
```

---

## 十、發證單位驗證學生經歷

B 發證單位端會使用此功能。

### 合約函式

```solidity
verifyExperience(uint256 tokenId)
```

### cast 測試範例

用 Account 1 驗證 Token ID 0：

```bash
cast send <ANVIL_CONTRACT_ADDRESS> "verifyExperience(uint256)" 0 --rpc-url http://127.0.0.1:8545 --private-key 0x59c6995e998f97a5a0044966f094538c9e86dae4528a3b3d9ff64b0b7a08a9d
```

驗證成功後，status 會從：

```text
1 = Pending
```

變成：

```text
2 = Verified
```

---

## 十一、發證單位直接發證

B 發證單位端也可以直接發行一筆已驗證經歷。

### 合約函式

```solidity
issueBadge(address student, bytes32 certHash, string category, string experienceType)
```

### cast 測試範例

```bash
cast send <ANVIL_CONTRACT_ADDRESS> "issueBadge(address,bytes32,string,string)" 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC <CERT_HASH> "活動參與" "區塊鏈工作坊" --rpc-url http://127.0.0.1:8545 --private-key 0x59c6995e998f97a5a0044966f094538c9e86dae4528a3b3d9ff64b0b7a08a9d
```

此功能會直接建立一筆：

```text
Verified
```

狀態的經歷。

---

## 十二、拒絕驗證

B 發證單位端會使用此功能。

### 合約函式

```solidity
rejectExperience(uint256 tokenId)
```

### cast 測試範例

```bash
cast send <ANVIL_CONTRACT_ADDRESS> "rejectExperience(uint256)" 0 --rpc-url http://127.0.0.1:8545 --private-key 0x59c6995e998f97a5a0044966f094538c9e86dae4528a3b3d9ff64b0b7a08a9d
```

成功後，status 會變成：

```text
3 = Rejected
```

---

## 十三、撤銷已驗證經歷

B 發證單位端會使用此功能。

### 合約函式

```solidity
revokeBadge(uint256 tokenId)
```

### cast 測試範例

```bash
cast send <ANVIL_CONTRACT_ADDRESS> "revokeBadge(uint256)" 0 --rpc-url http://127.0.0.1:8545 --private-key 0x59c6995e998f97a5a0044966f094538c9e86dae4528a3b3d9ff64b0b7a08a9d
```

成功後，status 會變成：

```text
4 = Revoked
```

---

## 十四、部署到 Sepolia 測試鏈

Demo 建議使用 Sepolia，讓所有組員共用同一份合約。

### 1. 設定 RPC URL

```bash
export SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
```

### 2. 設定部署錢包 private key

請使用測試用錢包，不要使用真正存放資產的主錢包。

```bash
export PRIVATE_KEY=你的Sepolia測試錢包PrivateKey
```

不要加 `< >`。

不要把 private key commit 到 GitHub。

### 3. 部署合約

```bash
forge create src/BadgeNFT.sol:BadgeNFT --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY --broadcast
```

成功後記下：

```text
Deployed to: 0x...
```

這就是：

```text
SEPOLIA_CONTRACT_ADDRESS
```

---

## 十五、Sepolia 上新增發證單位

假設 B 的發證單位錢包地址是：

```text
<B_ISSUER_ADDRESS>
```

由合約 owner 執行：

```bash
cast send <SEPOLIA_CONTRACT_ADDRESS> "approveIssuer(address)" <B_ISSUER_ADDRESS> --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY
```

檢查：

```bash
cast call <SEPOLIA_CONTRACT_ADDRESS> "approvedIssuers(address)(bool)" <B_ISSUER_ADDRESS> --rpc-url $SEPOLIA_RPC_URL
```

回傳 `true` 代表成功。

---

## 十六、提供給 B / C / D 的共同設定

前端共用設定建議放在：

```text
frontend/shared/config.js
```

```javascript
export const CONTRACT_ADDRESS = "0x你的Sepolia合約地址";
export const CHAIN_ID = 11155111;
export const RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com";
```

ABI 建議放在：

```text
frontend/shared/abi.js
```

```javascript
export const badgeNFTAbi = [
  // 貼上 out/BadgeNFT.sol/BadgeNFT.json 裡面的 abi 陣列
];
```

---

## 十七、B 組前端串接方式

B 需要 MetaMask，並使用 signer 呼叫合約。

```javascript
import { ethers } from "ethers";
import { badgeNFTAbi } from "../shared/abi.js";
import { CONTRACT_ADDRESS } from "../shared/config.js";

let provider;
let signer;
let contract;

async function connectWallet() {
  provider = new ethers.BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);

  signer = await provider.getSigner();

  contract = new ethers.Contract(
    CONTRACT_ADDRESS,
    badgeNFTAbi,
    signer
  );

  const address = await signer.getAddress();
  console.log("Connected issuer:", address);
}
```

B 主要使用：

```text
issueBadge(...)
verifyExperience(...)
rejectExperience(...)
revokeBadge(...)
approvedIssuers(...)
getExperience(...)
```

---

## 十八、C 組前端串接方式

C 需要 MetaMask，並使用 signer 呼叫合約。

```javascript
import { ethers } from "ethers";
import { badgeNFTAbi } from "../shared/abi.js";
import { CONTRACT_ADDRESS } from "../shared/config.js";

let provider;
let signer;
let contract;

async function connectWallet() {
  provider = new ethers.BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);

  signer = await provider.getSigner();

  contract = new ethers.Contract(
    CONTRACT_ADDRESS,
    badgeNFTAbi,
    signer
  );

  const address = await signer.getAddress();
  console.log("Connected student:", address);
}
```

C 主要使用：

```text
submitExperience(...)
getStudentExperiences(...)
getExperience(...)
```

---

## 十九、D 組前端串接方式

D 不需要 MetaMask，因為只讀鏈上資料。

```javascript
import { ethers } from "ethers";
import { badgeNFTAbi } from "../shared/abi.js";
import { CONTRACT_ADDRESS, RPC_URL } from "../shared/config.js";

const provider = new ethers.JsonRpcProvider(RPC_URL);

const contract = new ethers.Contract(
  CONTRACT_ADDRESS,
  badgeNFTAbi,
  provider
);
```

D 主要使用：

```text
getExperience(...)
approvedIssuers(...)
```

驗證邏輯：

```javascript
async function verifyToken(tokenId, rawText) {
  const exp = await contract.getExperience(tokenId);

  const chainHash = exp.certHash;
  const localHash = ethers.keccak256(ethers.toUtf8Bytes(rawText));

  const issuer = exp.issuer;
  const status = Number(exp.status);

  const hashMatched = chainHash === localHash;
  const isVerified = status === 2;
  const issuerTrusted = await contract.approvedIssuers(issuer);

  if (hashMatched && isVerified && issuerTrusted) {
    return "驗證成功：此經歷內容未被竄改，且已由可信單位驗證";
  }

  if (!hashMatched) {
    return "驗證失敗：資料內容可能被修改";
  }

  if (!isVerified) {
    return "此經歷尚未通過驗證或已被撤銷";
  }

  if (!issuerTrusted) {
    return "發證單位目前不在可信白名單中";
  }
}
```

---

## 二十、Demo 建議流程

### 1. 學生自行上傳經歷

```text
學生連接 MetaMask
→ 填寫經歷資料
→ 前端產生 certHash
→ 呼叫 submitExperience
→ 狀態顯示 Pending
```

### 2. 發證單位驗證

```text
發證單位連接 MetaMask
→ 查看學生提交的 tokenId
→ 呼叫 verifyExperience
→ 狀態變成 Verified
```

### 3. 學生能力護照展示

```text
學生查看自己的所有經歷
→ 顯示經歷卡片
→ 狀態顯示 Verified
→ 產生 QR Code
```

### 4. 驗證者查驗

```text
驗證者開啟驗證頁
→ 不需要連接 MetaMask
→ 查詢 tokenId
→ 重新計算 hash
→ 比對鏈上 certHash
→ 檢查 status 與 issuer
→ 顯示驗證成功或失敗
```

---

## 二十一、注意事項

### 1. 不要上傳 private key

請勿將以下內容推上 GitHub：

```text
.env
private key
seed phrase
MetaMask 助記詞
```

### 2. 合約修改後要重新部署

只要 `BadgeNFT.sol` 有改：

```text
forge build
→ forge create
→ 得到新的 contract address
→ B / C / D 更新 config.js
```

### 3. Demo 時只需要一個 Sepolia 合約

B、C、D 都應該使用同一個：

```text
Sepolia contract address
同一份 ABI
同一個 RPC URL
```

### 4. Anvil 只適合本地測試

如果每個人都用自己的 Anvil，大家的資料不會共用。

Demo 建議使用 Sepolia。
