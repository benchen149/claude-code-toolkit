# claude-usage-bar

Ubuntu 上的浮動視窗,即時顯示 Claude Code 的 `/usage` 額度使用狀況(session % 與週用量 %)。

## 安裝

Ubuntu 上 `tkinter` 是獨立的系統套件,預設不會隨 Python 安裝,請先安裝:

```bash
sudo apt install python3-tk
```

### 方式一:pipx(推薦,裝成全域指令)

裝完後不用 `cd` 進資料夾、不用 `source venv`,在任何地方都能直接打 `claude-usage-bar`。

```bash
sudo apt install pipx
pipx install ./packages/usage-bar
```

之後 repo 有更新,重新安裝最新版:

```bash
pipx install ./packages/usage-bar --force
```

### 方式二:venv(開發/跑測試用)

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

- `--interval SECONDS`:每次刷新**完成後**的等待秒數,預設 60,須為正整數。這不是嚴格的週期 ── 實際週期大約是「抓取時間 + interval」(抓取本身通常很快,遠低於 1 秒)。
- `--position {top-right,top-left,bottom-right,bottom-left}`:視窗初始位置,預設 top-right。在多螢幕環境下,角落位置是相對於*整個虛擬螢幕*(所有螢幕合併後的範圍)計算的 ── 例如 "top-right" 會落在最右側的螢幕上,不一定是你正在看的那個螢幕。這是 Tk/X11 的限制,不是 bug;之後都可以直接拖曳視窗移動。
- `--foreground`:預設執行時會自動轉背景(像自己加了 `&`),終端機馬上拿回控制權。加這個參數維持原本會卡住終端機的行為,方便除錯或需要看 exit code 的時候用。

視窗無邊框、常駐最上層,可用滑鼠拖曳移動,右鍵選單可結束程式。

### 已知限制

- **Esc 鍵不保證一定按得到**:在 focus-follows-mouse(滑鼠移到哪、鍵盤焦點就跟到哪)的桌面環境下,視窗剛開啟時 Esc 有效,但只要你把滑鼠移去操作別的視窗,焦點就跟著跑掉,Esc 就按不到了。**右鍵選單是比較可靠的結束方式**,不依賴目前誰持有鍵盤焦點。
- **`-topmost` 不保證一定蓋得住所有視窗**:某些全螢幕應用程式(例如瀏覽器全螢幕播放影片)可能會被桌面環境特別拉到最上層,蓋住這個浮動視窗。遇到這種狀況,先讓蓋住的視窗離開全螢幕,或用 `ps aux | grep claude-usage-bar` 找到 PID 用 `kill` 結束。

## 測試

```bash
pytest -v
```
