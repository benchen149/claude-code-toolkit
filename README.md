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

## 共用 slash command

[`shared/commands/`](shared/commands/) 底下是可在任何 repo 使用的 slash command,裝到 `~/.claude/commands/` 後所有專案都能用。

| Command | 說明 |
|---|---|
| [`/github-flow`](shared/commands/github-flow.md) | issue → branch → PR → merge 流程;自動偵測 repo,一律採用 main + develop 分支模型(缺 `develop` 時會詢問後建立) |

**本機有 clone 這個 repo**:用 symlink,`git pull` 後自動更新:

```bash
mkdir -p ~/.claude/commands && ln -s /path/to/claude-code-toolkit/shared/commands/github-flow.md ~/.claude/commands/github-flow.md
```

**其他電腦(沒有 clone)**:

```bash
mkdir -p ~/.claude/commands && curl -fsSL https://raw.githubusercontent.com/benchen149/claude-code-toolkit/main/shared/commands/github-flow.md -o ~/.claude/commands/github-flow.md
```

## 結構

```
claude-code-toolkit/
  docs/superpowers/specs/   # 各工具的設計文件
  packages/
    usage-bar/               # 第一個工具
  shared/
    CLAUDE.md                # 共用程式碼修改原則
    commands/                # 共用 slash command
```
