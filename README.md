# claude-code-toolkit

跟 [Claude Code](https://claude.com/claude-code) 搭配使用的小工具集合(monorepo)。每個工具各自獨立成一個 package,放在 `packages/` 底下。

## Packages

| 名稱 | 說明 |
|---|---|
| [`usage-bar`](packages/usage-bar/) | Ubuntu 上的浮動視窗,即時顯示 Claude Code 的 `/usage` 額度使用狀況。 |

## 共用程式碼修改原則

[`shared/CLAUDE.md`](shared/CLAUDE.md) 是跨專案、跨電腦共用的 Claude 程式碼修改原則(取自 [Karpathy guidelines](https://github.com/multica-ai/andrej-karpathy-skills)),不依賴任何 plugin。放進使用者層級的 `~/.claude/CLAUDE.md` 後,該電腦上所有專案都會生效。

**本機有 clone 這個 repo**:在 `~/.claude/CLAUDE.md` 加一行 import,`git pull` 後自動更新:

```markdown
@/path/to/claude-code-toolkit/shared/CLAUDE.md
```

**其他電腦(沒有 clone)**:直接從 GitHub 附加到 `~/.claude/CLAUDE.md`:

```bash
mkdir -p ~/.claude && curl -fsSL https://raw.githubusercontent.com/benchen149/claude-code-toolkit/main/shared/CLAUDE.md >> ~/.claude/CLAUDE.md
```

這種方式不會自動更新;原則有修改時,先刪掉 `~/.claude/CLAUDE.md` 裡的舊段落再重跑一次。

## 結構

```
claude-code-toolkit/
  docs/superpowers/specs/   # 各工具的設計文件
  packages/
    usage-bar/               # 第一個工具
  shared/
    CLAUDE.md                # 共用程式碼修改原則
```
