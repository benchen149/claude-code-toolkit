---
name: discuss
description: 記錄討論並產生討論文件到 discuss-notes 目錄（由環境變數 DISCUSS_NOTES_DIR 指定）。當使用者說「我要討論 XXX，請幫我紀錄」、「來討論 XXX 並紀錄」、「想聊聊 XXX，幫我記錄下來」時使用；使用者說「討論結束，請提交」時，執行收尾（確認後 git commit + push）。
---

# discuss

把使用者提出的討論主題，整理成 Markdown 文件，存到 `$DISCUSS_NOTES_DIR`。

## When to use

- 開始：「我要討論 XXX，請幫我紀錄」及類似說法
- 收尾：「討論結束，請提交」

使用者只是一般提問、沒有要求紀錄時，不要使用這個 skill。

## Output location

環境變數 `DISCUSS_NOTES_DIR` 指向的目錄（獨立 git repo，只有 `main` 分支），各電腦在 `~/.claude/settings.json` 的 `env` 自行設定。

- 開始前用 `echo "$DISCUSS_NOTES_DIR"` 確認；未設定、或目錄不存在時，**停下來告知使用者並詢問路徑，不自行猜測**
- 確認後讀該 repo 的 `CLAUDE.md`，以它為準

## Filename rule

`YYYY-MM-DD-discussion-<slug>.md`

- 全部英文、數字、連字號，不用空格、底線、中文；專有名詞轉小寫
- `slug` 由討論主題決定，3 到 6 個單字
- **建檔前先提出 1 到 2 個檔名建議，使用者確認（或指定）後才建檔**
- 同名檔案已存在時不覆蓋，詢問使用者要追加還是換名

## Document template

以 `templates/discussion.md` 為準：檔頭（日期、狀態、相關專案、參考），以及 `Background`、`Discussion`、`Decisions`、`Open Questions`、`Action Items`、`References`。

- 內容用繁體中文，區段標題保持英文
- 記錄重點與取捨，不是逐字對話
- 只在結論形成時更新 `Decisions`、`Open Questions`、`Action Items`，不用每句話都寫

## Workflow

1. 確認主題，提出檔名建議，等使用者確認
2. 依範本建檔，邊討論邊整理
3. 使用者要求時回報目前檔案路徑與狀態
4. 使用者說「討論結束，請提交」→ 走下方收尾流程

## Wrap-up（收尾：僅在使用者說「討論結束，請提交」時）

1. 最後整理文件：補齊 `Decisions`、`Open Questions`、`Action Items`，把檔頭「狀態」更新
2. push 前檢查（只讀）：
   - 遠端是否為 private：`gh repo view --json visibility`
   - 文件是否有疑似 token、密碼、私鑰的字串（如 `ghp_`、`glpat-`、`gho_`、`BEGIN ... PRIVATE KEY`、`password`、`token=`）
   - 是否有遠端 `origin`
3. **用純文字列出將執行的內容，並等使用者回覆 `y`**，格式：

   ```
   即將執行:
   - 檔案: <檔名>
   - commit 訊息: docs: add discussion on <主題>
   - 遠端: <owner/repo>（private ✓ / ⚠️ public）
   - 敏感字串檢查: 未發現 ✓ / ⚠️ 發現 <內容>
   - 指令: git add <該檔案> && git commit && git push origin main

   是否要自動 commit + push? (y / n)
   ```

4. 只有在**緊接著的下一則使用者訊息**是明確的 `y`（或「是」「好」）才執行；其他回覆（含 `n`、修改要求、不相干的話）一律不執行，改為處理該回覆
5. 執行時：
   - `git add` 只加這一份文件，不用 `git add -A` 或 `git add .`
   - commit 訊息依照對話 system-reminder 的規則附上 Co-Authored-By
   - `git push origin main`，**不使用 `--force`**
6. 回報 commit hash 與 push 結果

### 失敗與例外

- 遠端是 public、或發現疑似敏感字串：在提示裡標出並建議不要 push，不自行放行
- 沒有遠端或認證失敗：保留本機 commit，說明原因，不改用其他方式
- push 被拒：不強推，回報給使用者
- 文件與檔名規則不符：先停下來詢問

## Rules

- 平常寫檔時**不碰 git**，只有收尾流程且使用者回覆 `y` 後才 commit/push
- 不建立分支、不開 issue、不開 PR
- 這個授權只限於 `discuss-notes` repo，不延伸到其他 repo
