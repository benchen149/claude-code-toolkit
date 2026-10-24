# GitHub SSH 環境初始化

在新的本地開發環境中，完成 SSH key 產生、GitHub 帳號綁定、gh CLI 登入的一次性設定，使後續可直接執行 `/github-flow`。

**每台電腦只需執行一次**；除了 Step 7（切換 remote），其餘設定都是整台電腦共用，不需每個 repo 重做。

## 使用方式

```
/setup-github-ssh
```

## 互動式指令由使用者執行

`ssh-keygen`（輸入 passphrase）、`ssh -T`（解鎖 key）、`gh auth login`（貼上 token）都需要互動輸入，Claude 的 Bash 無法執行。遇到這些步驟時，**提示使用者在 prompt 輸入 `! <指令>` 自行執行**，執行完再由 Claude 驗證結果。

**絕對不可要求使用者把 token 或 passphrase 貼進對話**，避免留在對話紀錄中。

## 執行流程

### Step 1：確認環境資訊

詢問使用者：
- **GitHub 帳號 email**（用於 SSH key comment 與 git config）
- **GitHub 帳號 username**（用於 git config）

若目前在 git repo 內，讀取 remote URL 供 Step 7 使用：

```bash
git remote get-url origin
```

---

### Step 2：安裝 gh CLI（若尚未安裝）

**不可直接 pipe curl 到 sudo**，先下載再安裝，避免供應鏈攻擊（以下為 Debian / Ubuntu 的 apt 安裝方式）：

```bash
if ! command -v gh &>/dev/null; then
  # 下載 GPG keyring 到暫存檔，勿直接 pipe 進 sudo
  KEYRING=$(mktemp)
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o "$KEYRING"

  # 確認為合法 GPG keyring，再寫入系統
  file "$KEYRING" | grep -q "PGP\|GPG" || {
    echo "ERROR: 下載的 keyring 格式異常，中止安裝"; rm -f "$KEYRING"; exit 1
  }

  sudo cp "$KEYRING" /usr/share/keyrings/githubcli-archive-keyring.gpg
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  rm -f "$KEYRING"

  echo "deb [arch=$(dpkg --print-architecture) \
    signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
    https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

  sudo apt update -qq && sudo apt install gh -y -qq
fi
```

---

### Step 3：產生 SSH key（若 `~/.ssh/id_ed25519` 不存在）

```bash
test -f ~/.ssh/id_ed25519 && echo "已存在，跳過 Step 3"
```

不存在時，提示使用者自行執行（**必須設定 passphrase**，保護 private key 在機器被入侵時不被直接使用）：

```
! ssh-keygen -t ed25519 -C "<EMAIL>" -f ~/.ssh/id_ed25519
```

完成後顯示公鑰，提示使用者複製：

```bash
cat ~/.ssh/id_ed25519.pub
```

---

### Step 4：加入 GitHub known_hosts 並驗證 fingerprint

若 `known_hosts` 已有 github.com，跳過此步驟，避免重複寫入：

```bash
ssh-keygen -F github.com >/dev/null && echo "已存在，跳過 Step 4"
```

**不可直接信任 ssh-keyscan 的結果**，需對比 GitHub 官方公佈的 fingerprint：

```bash
# 下載到暫存檔，先驗證再加入
HOST_KEYS=$(mktemp)
ssh-keyscan github.com > "$HOST_KEYS" 2>/dev/null
ssh-keygen -lf "$HOST_KEYS"
```

人工確認輸出的 fingerprint 是否符合 GitHub 官方值（來源：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints）：

```
SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s  (RSA)
SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM  (ECDSA)
SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU  (Ed25519)
```

確認符合後，再加入 known_hosts：

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cat "$HOST_KEYS" >> ~/.ssh/known_hosts
rm -f "$HOST_KEYS"
```

---

### Step 5：將公鑰加入 GitHub 帳號（需使用者操作）

提示使用者前往：

```
https://github.com/settings/ssh/new
```

- **Title**：填入可識別的機器名稱（`hostname` 指令取得）
- **Key type**：Authentication Key
- **Key**：貼上 Step 3 顯示的公鑰

等待使用者確認完成後繼續。

---

### Step 6：測試 SSH 連線

提示使用者自行執行（會要求輸入 passphrase 解鎖 key）：

```
! ssh -T git@github.com
```

預期出現：`Hi <username>! You've successfully authenticated`（此指令成功時 exit code 也是 1，以輸出文字判斷）

若失敗，提示使用者確認 Step 5 是否完成後重試。

---

### Step 7：切換 git remote 為 SSH（僅限在 repo 內執行時）

若 Step 1 讀到的 remote 是 `https://github.com/` 開頭才需要執行；每個要改用 SSH 的 repo 各執行一次：

```bash
CURRENT=$(git remote get-url origin)
SSH_URL=$(echo "$CURRENT" | sed 's|https://github.com/|git@github.com:|')
git remote set-url origin "$SSH_URL"
git remote get-url origin  # 確認輸出為 git@github.com:... 格式
```

---

### Step 8：gh CLI 登入（使用 Fine-grained Token，最小權限原則）

**不建議使用 classic token 的 `repo` scope**，應改用 **Fine-grained Personal Access Token**，只給必要權限。

`gh` 每台電腦只會保存一組 github.com 登入，所有 repo 共用，因此 **token 以「一台電腦一個」為單位**，涵蓋這台電腦要開發的所有 repo；若只選單一 repo，其他 repo 執行 `/github-flow` 會因權限不足而失敗。

#### 產生 Fine-grained Token 步驟：

1. 前往 `https://github.com/settings/personal-access-tokens/new`
2. **Token name**：以電腦命名（如 `<hostname>-claude`）
3. **Expiration**：建議 90 天，到期需重新產生
4. **Resource owner**：選擇 repo 的擁有者（個人帳號或組織）
5. **Repository access**：選 `All repositories`，或 `Only select repositories` 並勾選這台電腦要開發的所有 repo
6. **Repository permissions** 最小所需權限：
   - Contents：**Read and write**
   - Issues：**Read and write**
   - Pull requests：**Read and write**
   - Metadata：**Read-only**（自動勾選）
7. 產生後複製 token（只顯示一次）

#### 使用 token 登入：

提示使用者自行執行，依提示選擇 **Paste an authentication token** 後貼上 token：

```
! gh auth login --hostname github.com --git-protocol ssh
```

確認登入狀態與權限：

```bash
gh auth status
```

---

### Step 9：設定 git 身份

```bash
git config --global user.email "$EMAIL"
git config --global user.name "$USERNAME"
```

---

### Step 10：驗證完整環境

```bash
ssh -T git@github.com 2>&1  # 應出現 Hi <username>!
gh auth status              # 應顯示 Logged in to github.com
git config user.email       # 應顯示正確 email
git remote get-url origin   # 在 repo 內執行 Step 7 後，應為 git@github.com:... 格式
```

全部通過後提示：環境設定完成，可執行 `/github-flow`。

---

## 安全注意事項

| 項目 | 規範 |
|------|------|
| SSH key passphrase | 必須設定，不可留空 |
| Token / passphrase | 由使用者以 `!` 自行輸入，不可貼進對話 |
| known_hosts | 加入前必須對比 GitHub 官方 fingerprint |
| gh CLI 安裝 | 先下載驗證 GPG keyring 格式，再寫入系統 |
| 暫存檔 | 使用 `mktemp`，不使用固定的 `/tmp` 路徑 |
| Token 類型 | 使用 Fine-grained Token，只給 Contents / Issues / Pull requests 讀寫 |
| Token 範圍 | 一台電腦一個，涵蓋要開發的 repo，不給多餘的 repo 或權限 |
| Token 有效期 | 建議 90 天，到期重新產生 |
| Token 儲存 | `~/.config/gh/hosts.yml` 為明文，不可納入 git / dotfiles repo / backup |
| SSH private key | `~/.ssh/id_ed25519` 不可複製到他處、不可提交至任何 repo |

## 注意事項

- SSH key 只需產生一次；若 `~/.ssh/id_ed25519` 已存在，跳過 Step 3
- 若桌面環境沒有自動啟動 ssh-agent，每次使用 SSH 時都會要求輸入 passphrase；可在終端機執行 `eval "$(ssh-agent -s)" && ssh-add` 讓當前 session 免重複輸入
- 此 command 不會建立、切換或刪除任何 branch
