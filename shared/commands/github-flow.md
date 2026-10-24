# GitHub Flow 自動化

執行完整的 GitHub issue → branch → PR → merge 工作流程，或關閉指定的 PR / Issue。適用於任何 GitHub repo。

用 `gh` CLI（已登入帳號操作，不需要另外設定 `GITHUB_TOKEN`）。

## 使用方式

```
/github-flow
```

執行後會詢問要執行哪個模式。

---

## Step 0：偵測 repo 設定（兩種模式都要先做）

```bash
gh auth status
gh repo view --json nameWithOwner,defaultBranchRef \
  -q '.nameWithOwner + " " + .defaultBranchRef.name'
git ls-remote --exit-code --heads origin develop
```

- 第一個值記為 `$REPO`（例如 `owner/name`），第二個值記為 `$DEFAULT_BRANCH`（例如 `main`）
- `git ls-remote` exit code 為 0 代表 remote 有 `develop` branch
- 若 `gh auth status` 顯示未登入，先提示使用者執行 `gh auth login`

**分支模型**：
- **有 `develop`**：維持 `$DEFAULT_BRANCH`（穩定）與 `develop`（整合）兩條長期分支。Feature branch 從 `develop` 切出、PR 合回 `develop`；要併進 `$DEFAULT_BRANCH` 時另外開 sync PR（見 Step 8）
- **沒有 `develop`**：Feature branch 直接從 `$DEFAULT_BRANCH` 切出、PR 合回 `$DEFAULT_BRANCH`，略過 Step 8

---

## 模式一：完整開發流程（issue → branch → PR → merge）

### Step 1：收集資訊
詢問使用者：
- **Issue 標題**（例如：`feat: add xxx`，**標題一律使用英文**）
- **Issue 描述**（問題背景、預計異動）
- **Branch slug**（例如：`add-xxx`，會自動加上 issue 編號變成 `{number}-add-xxx`）
- **目標 base branch**（有 `develop` 時預設 `develop`，否則預設 `$DEFAULT_BRANCH`）— feature branch 從此 branch 切出，PR 也 merge 回此 branch

### Step 2：開 GitHub Issue
```bash
gh issue create \
  --repo $REPO \
  --title "$TITLE" \
  --body "$BODY"
```
從輸出的 URL 取得 issue 編號（URL 結尾的數字）。

### Step 3：建立並切換 branch（自動執行，不需使用者確認）
取得 issue 編號後立即執行，無需等待使用者確認。

```bash
git checkout $BASE_BRANCH
git pull origin $BASE_BRANCH
git checkout -b {issue-number}-$SLUG
```

### Step 4：等待使用者完成改動
提示使用者進行程式碼修改，完成後告知 Claude 繼續。

### Step 4.5：Diff 自我檢查
Commit 前執行 `git diff $BASE_BRANCH`（含未 commit 的改動）和 `git status`（看新增檔案），逐一確認：
- 每個改動都能對應到 issue 描述；無關的改動要退回或另開 issue
- 沒有順手做的格式或重構變更
- 沒有殘留因本次改動而未使用的 import／變數

有疑慮的地方列出來給使用者確認，再進入 Step 5。

### Step 5：Commit & Push
```bash
git add <changed files>
git commit -m "feat/fix/chore: $TITLE

$DESCRIPTION

Closes #{issue-number}"
git push origin {issue-number}-$SLUG
```

### Step 6：開 Pull Request
```bash
gh pr create \
  --repo $REPO \
  --title "$TITLE" \
  --body "$BODY" \
  --head {issue-number}-$SLUG \
  --base $BASE_BRANCH
```

### Step 7：確認是否 merge
詢問使用者是否直接 merge，若是則：
```bash
gh pr merge {pr-number} --repo $REPO --merge
git checkout $BASE_BRANCH
git pull origin $BASE_BRANCH
git branch -d {issue-number}-$SLUG
git push origin --delete {issue-number}-$SLUG
```
- merge 後自動刪除 feature branch（local + remote），無需詢問使用者
- **絕對不可刪除** `$DEFAULT_BRANCH`、`develop` 等長期 branch，只刪除格式為 `{issue-number}-$SLUG` 的 feature branch

### Step 8：sync develop 到 $DEFAULT_BRANCH（選用，僅限 base branch 是 `develop`）
詢問是否開一個 sync PR 將變更合併進 `$DEFAULT_BRANCH`。

開 sync PR 時**必須**在 body 帶入本次相關的 `Closes #X`，讓 GitHub 在 merge 進 `$DEFAULT_BRANCH` 時自動關閉 issue：

```bash
gh pr create \
  --repo $REPO \
  --title "chore: sync develop changes to $DEFAULT_BRANCH" \
  --body "Closes #{issue-number}" \
  --head develop \
  --base $DEFAULT_BRANCH
```

> **原因**：GitHub 的 `Closes #X` 只在 PR merge 進 default branch 時觸發，feature branch → `develop` 不會自動關閉 issue。

---

## Issue 標題準則

- **一律使用英文**撰寫 issue 標題
- 格式：`<type>: <short description>`，例如 `feat: add xxx`、`fix: xxx not working`、`chore: update xxx`

---

## 模式二：關閉 PR / Issue

詢問使用者要關閉的類型（PR 或 Issue）與編號，支援一次關閉多個。

### 關閉 Issue
```bash
gh issue close {number} --repo $REPO
```

### 關閉 PR
```bash
gh pr close {number} --repo $REPO
```

---

## 注意事項

- 操作者需要已用 `gh auth login` 登入，且帳號對 `$REPO` 有 Issues / Pull requests / Contents 的寫入權限
- 必須在有 GitHub remote（`origin`）的 git repo 裡執行
- feature branch merge 後自動刪除（local + remote），`$DEFAULT_BRANCH`、`develop` 等長期 branch 不在自動刪除範圍內
