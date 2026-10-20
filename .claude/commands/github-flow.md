# GitHub Flow 自動化

執行完整的 GitHub issue → branch → PR → merge 工作流程，或關閉指定的 PR / Issue。

本專案維持 `main`（穩定）與 `develop`（整合）兩條長期分支。Feature branch 一律從 `develop` 切出、PR 合回 `develop`；`develop` 要併進 `main` 時另外開一個 sync PR（見模式一 Step 8）。

用 `gh` CLI（已登入帳號操作，不需要另外設定 `GITHUB_TOKEN`）。

## 使用方式

```
/github-flow
```

執行後會詢問要執行哪個模式。

---

## 模式一：完整開發流程（issue → branch → PR → merge）

### Step 1：收集資訊
詢問使用者：
- **Issue 標題**（例如：`feat: add xxx`，**標題一律使用英文**）
- **Issue 描述**（問題背景、預計異動）
- **Branch slug**（例如：`add-xxx`，會自動加上 issue 編號變成 `{number}-add-xxx`）
- **目標 base branch**（預設 `develop`）— feature branch 從此 branch 切出，PR 也 merge 回此 branch

### Step 2：開 GitHub Issue
```bash
gh issue create \
  --repo benchen149/claude-code-toolkit \
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
  --repo benchen149/claude-code-toolkit \
  --title "$TITLE" \
  --body "$BODY" \
  --head {issue-number}-$SLUG \
  --base $BASE_BRANCH
```

### Step 7：確認是否 merge
詢問使用者是否直接 merge，若是則：
```bash
gh pr merge {pr-number} --repo benchen149/claude-code-toolkit --merge
git checkout $BASE_BRANCH
git pull origin $BASE_BRANCH
git branch -d {issue-number}-$SLUG
git push origin --delete {issue-number}-$SLUG
```
- merge 後自動刪除 feature branch（local + remote），無需詢問使用者
- **絕對不可刪除** `develop`、`main` 等長期 branch，只刪除格式為 `{issue-number}-$SLUG` 的 feature branch

### Step 8：sync develop 到 main（選用）
若 base branch 是 `develop`，詢問是否開一個 sync PR 將變更合併進 `main`。

開 sync PR 時**必須**在 body 帶入本次相關的 `Closes #X`，讓 GitHub 在 merge 進 main 時自動關閉 issue：

```bash
gh pr create \
  --repo benchen149/claude-code-toolkit \
  --title "chore: sync develop changes to main" \
  --body "Closes #{issue-number}" \
  --head develop \
  --base main
```

> **原因**：GitHub 的 `Closes #X` 只在 PR merge 進 default branch（`main`）時觸發，feature branch → `develop` 不會自動關閉 issue。

---

## Issue 標題準則

- **一律使用英文**撰寫 issue 標題
- 格式：`<type>: <short description>`，例如 `feat: add xxx`、`fix: xxx not working`、`chore: update xxx`

---

## 模式二：關閉 PR / Issue

詢問使用者要關閉的類型（PR 或 Issue）與編號，支援一次關閉多個。

### 關閉 Issue
```bash
gh issue close {number} --repo benchen149/claude-code-toolkit
```

### 關閉 PR
```bash
gh pr close {number} --repo benchen149/claude-code-toolkit
```

---

## 注意事項

- 操作者需要已用 `gh auth login` 登入，且帳號對 `benchen149/claude-code-toolkit` 有 Issues / Pull requests / Contents 的寫入權限
- 若 `gh auth status` 顯示未登入，流程開始前會提示先登入
- base branch 預設為 `develop`，若要直接 merge 到 `main` 請在 Step 1 指定
- feature branch merge 後自動刪除（local + remote），`develop`、`main` 等長期 branch 不在自動刪除範圍內
