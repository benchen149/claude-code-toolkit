# usage-bar 設計文件

## 目標
在 Ubuntu 上,用 Python 寫一個浮動視窗,執行指令後跳出,顯示目前 Claude Code 的 `/usage` 額度使用狀況,並定期自動刷新。

## 背景與技術調查

使用者帳號是 **Pro 訂閱方案**(非 API 按量計費),所以 `/usage` 顯示的是「額度使用百分比 + 重置時間」,不是美金金額。

已驗證以下指令可以在本機直接取得 `/usage` 的輸出,且不會呼叫 API(`total_cost_usd: 0`、`duration_api_ms: 0`,`local_command: "usage"`):

```
claude -p "/usage" --output-format json
```

回應 JSON 的 `result` 欄位是純文字,格式類似:

```
Current session: 2% used · resets Oct 21, 3:10am (Asia/Taipei)
Current week (all models): 3% used · resets Oct 20, 11pm (Asia/Taipei)
...
```

因此不需要解析 `~/.claude/projects/*.jsonl` 裡的 token 用量(那條路線脆弱,還要自己維護模型價格表)。

## 架構

**技術選擇**:Python + Tkinter(標準庫內建,免裝系統套件,Ubuntu 任何桌面環境都能跑)。

曾考慮但不採用:
- GTK(PyGObject)— 視覺更原生,但需要 apt 裝系統套件,環境依賴重。
- 系統匣圖示 — 不符合「浮動視窗」的需求。

**資料流**:
1. 背景 thread 每隔 N 秒執行 `claude -p "/usage" --output-format json`(設 timeout,避免卡住)
2. 用 regex 解析 `result` 文字,取出:session 使用百分比、session 重置時間、週使用百分比(all models)、週重置時間
3. 更新浮動視窗上的文字
4. 單次刷新失敗時保留上一次數值,不讓視窗崩潰

**套件結構**(位於此 monorepo 的 `packages/usage-bar/`):
```
packages/usage-bar/
  claude_usage_bar/
    __init__.py
    cli.py           # entry point,處理 --interval、--position 等參數
    usage_fetcher.py # subprocess 呼叫 + regex 解析 → dataclass
    ui.py            # Tkinter 浮動視窗
  tests/
    test_usage_fetcher.py
  pyproject.toml     # 封裝成 `claude-usage-bar` 指令
  README.md
```

**視窗外觀與互動**:
- 無邊框(`overrideredirect`)、常駐最上層(`-topmost`)、預設顯示在螢幕右上角
- 可用滑鼠拖曳移動視窗
- 顯示內容:`Session: 2% · Week: 3%`,兩個數字各自依自己的百分比獨立變色提示(綠 <50% / 黃 50-80% / 紅 >80%)
- 右鍵選單或「×」按鈕 / Esc 鍵可結束程式

**CLI 參數**(entry point:`claude-usage-bar`):
- `--interval SECONDS`(預設 60)— 控制重新抓取頻率
- `--position {top-right,top-left,bottom-right,bottom-left}`(預設 top-right)

**錯誤處理**:
- 找不到 `claude` 指令 → 顯示錯誤訊息後結束程式
- 單次刷新失敗/逾時 → 保留上一次數值,視窗上顯示小小「⚠」標記,下個週期自動重試

## 測試

- `usage_fetcher.py` 的 regex 解析邏輯寫單元測試,用錄下來的樣本文字當 fixture,涵蓋正常格式與格式缺失的邊界情況。
- UI 部分用 `run` 技能實際啟動,目測確認外觀、拖曳、刷新行為是否正常。

## 工具鏈

目前 monorepo 先維持單純目錄結構,不引入 workspace 工具(如 uv workspace)。每個 package 各自有獨立的 `pyproject.toml`,之後若多個工具之間真的出現重複邏輯,再視情況抽成共用套件或改用 workspace 工具管理依賴。

## 範圍外(本次不做)

- 不支援其他作業系統(macOS/Windows)
- 不持久化視窗位置(每次啟動都回到預設位置)
- 不做系統匣整合
