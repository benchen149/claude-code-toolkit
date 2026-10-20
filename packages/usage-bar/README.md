# claude-usage-bar

Ubuntu 上的浮動視窗,即時顯示 Claude Code 的 `/usage` 額度使用狀況(session % 與週用量 %)。

## 安裝

```bash
cd packages/usage-bar
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 使用

```bash
claude-usage-bar
claude-usage-bar --interval 30 --position bottom-left
```

- `--interval SECONDS`:刷新間隔秒數,預設 60。
- `--position {top-right,top-left,bottom-right,bottom-left}`:視窗初始位置,預設 top-right。

視窗無邊框、常駐最上層,可用滑鼠拖曳移動。右鍵選單或 Esc 鍵可結束程式。

## 測試

```bash
pytest -v
```
