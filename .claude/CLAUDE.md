# claude-code-toolkit

## 專案慣例
- Monorepo：每個工具是 `packages/<name>/` 底下獨立的 Python package
- 設計文件在 `docs/superpowers/specs/`，實作計畫在 `docs/superpowers/plans/`
- 分支流程：feature 從 `develop` 切出、合回 `develop`，用 `/github-flow`
- 測試：在 `packages/<name>/` 底下執行 `pytest -v`

## 程式碼修改原則（取自 [Karpathy guidelines](https://github.com/multica-ai/andrej-karpathy-skills)）

### Simplicity First
- 不加沒被要求的功能、單次使用的抽象層、可設定化
- 不為不可能發生的情境寫錯誤處理
- 如果 200 行能寫成 50 行，就重寫

### Surgical Changes
- 不順手改善相鄰的程式碼、註解、格式；配合既有風格
- 發現無關的 dead code 只提出來，不要刪
- 只清掉「自己的改動」造成的未使用 import／變數
- 檢驗標準：每一行 diff 都要能追溯到需求

> Think Before Coding 與 Goal-Driven Execution 由 superpowers 的
> brainstorming / TDD / verification 處理，這裡不重複。
> Typo 這類小改動可自行判斷，不必走完整流程。
