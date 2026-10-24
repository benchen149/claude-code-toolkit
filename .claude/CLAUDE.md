# claude-code-toolkit

## 專案慣例
- Monorepo：每個工具是 `packages/<name>/` 底下獨立的 Python package
- 設計文件在 `docs/superpowers/specs/`，實作計畫在 `docs/superpowers/plans/`
- 分支流程：feature 從 `develop` 切出、合回 `develop`，用 `/github-flow`
- 測試：在 `packages/<name>/` 底下執行 `pytest -v`
- 共用程式碼修改原則在 `shared/CLAUDE.md`（各電腦透過 `~/.claude/CLAUDE.md` 載入，安裝方式見 README）
