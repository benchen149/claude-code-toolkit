# claude-code-toolkit

跟 [Claude Code](https://claude.com/claude-code) 搭配使用的小工具集合(monorepo)。每個工具各自獨立成一個 package,放在 `packages/` 底下。

## Packages

| 名稱 | 說明 |
|---|---|
| [`usage-bar`](packages/usage-bar/) | Ubuntu 上的浮動視窗,即時顯示 Claude Code 的 `/usage` 額度使用狀況。 |

## 結構

```
claude-code-toolkit/
  docs/superpowers/specs/   # 各工具的設計文件
  packages/
    usage-bar/               # 第一個工具
```
