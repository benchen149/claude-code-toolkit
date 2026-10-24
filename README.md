# claude-code-toolkit

跟 [Claude Code](https://claude.com/claude-code) 搭配使用的工具與共用設定。

## 內容

| 項目 | 說明 |
|---|---|
| [`packages/usage-bar`](packages/usage-bar/) | Ubuntu 上的浮動視窗,即時顯示 Claude Code 的 `/usage` 額度使用狀況 |
| [`shared/CLAUDE.md`](shared/CLAUDE.md) | 共用程式碼修改原則(取自 [Karpathy guidelines](https://github.com/multica-ai/andrej-karpathy-skills)),所有專案生效 |
| [`/github-flow`](shared/commands/github-flow.md) | issue → branch → PR → merge 流程,一律採用 `main` + `develop` |
| [`/setup-github-ssh`](shared/commands/setup-github-ssh.md) | 新電腦一次性設定:`gh`、SSH key、`gh` 登入、git 身份 |

## 情境一:新電腦(例如公司)

1. 安裝 Claude Code 與 `git`
2. 安裝共用設定(可重複執行;之後 toolkit 有新增 command 時再跑一次即可):

   ```bash
   git clone https://github.com/benchen149/claude-code-toolkit.git ~/git/claude-code-toolkit
   mkdir -p ~/.claude/commands
   L="@$HOME/git/claude-code-toolkit/shared/CLAUDE.md"
   grep -qxF "$L" ~/.claude/CLAUDE.md 2>/dev/null || echo "$L" >> ~/.claude/CLAUDE.md
   ln -sf ~/git/claude-code-toolkit/shared/commands/*.md ~/.claude/commands/
   ```

3. 開啟 `claude`,執行 `/setup-github-ssh` 完成 SSH key 與 `gh` 登入
4. 確認:`/memory` 有 `shared/CLAUDE.md`;輸入 `/` 看得到 `github-flow`、`setup-github-ssh`

## 情境二:新增 git repo

1. 建立 repo 並 clone(`--add-readme` 讓 `main` 有第一個 commit,才能從它建立 `develop`):

   ```bash
   cd ~/git
   gh repo create benchen149/<name> --public --add-readme --clone
   cd <name>
   ```

2. 建立 `develop`,並保護 `main` 與 `develop`(禁止刪除與 force push):

   ```bash
   git push origin main:develop
   for b in main develop; do
     echo '{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}' \
       | gh api -X PUT "repos/benchen149/<name>/branches/$b/protection" --input -
   done
   ```

3. 開啟 `claude`,開始開發:
   - `/init`:產生專案自己的 `CLAUDE.md`,只寫這個專案特有的內容(build、測試、目錄結構)
   - `/github-flow`:每次改動都走 issue → branch → PR → merge

不需要把 command 或原則複製進新 repo,它們已經在 `~/.claude/` 對所有 repo 生效。

## 更新共用設定

```bash
cd ~/git/claude-code-toolkit && git pull
```

原則與 command 是 import / symlink,`git pull` 後馬上生效。

## 結構

```
claude-code-toolkit/
  docs/superpowers/   # 設計文件與實作計畫
  packages/           # 各工具,每個獨立成一個 package
  shared/
    CLAUDE.md         # 共用程式碼修改原則
    commands/         # 共用 slash command
```
