# usage-bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `claude-usage-bar`, a Tkinter floating window that shows live Claude Code `/usage` quota status on Ubuntu.

**Architecture:** A background thread periodically shells out to `claude -p "/usage" --output-format json`, parses the plain-text `result` field with regex into a `UsageSnapshot`, and pushes it through a thread-safe queue to the Tkinter main loop, which updates a borderless always-on-top label pair.

**Tech Stack:** Python 3.10+, stdlib only (`tkinter`, `subprocess`, `argparse`, `threading`, `queue`, `re`), `pytest` for tests (dev-only dependency).

**Spec:** `docs/superpowers/specs/2026-10-20-claude-usage-bar-design.md`

## Global Constraints

- Linux/Ubuntu desktop only — no macOS/Windows handling.
- Stdlib only at runtime (Tkinter) — no extra runtime dependencies.
- Data source is fixed to `claude -p "/usage" --output-format json` — never call the real API or parse `~/.claude/projects/*.jsonl`.
- CLI command name is `claude-usage-bar`. Default `--interval` is `60`. Default `--position` is `top-right`.
- Window position is not persisted — each launch starts at the default position for the chosen `--position`.

---

## File Structure

```
packages/usage-bar/
  pyproject.toml
  README.md
  claude_usage_bar/
    __init__.py
    usage_fetcher.py   # subprocess call + regex parsing -> UsageSnapshot
    ui.py               # color/position math + FloatingBar Tkinter widget
    cli.py               # argparse + thread/queue wiring + entry point
  tests/
    test_usage_fetcher.py
    test_ui.py
    test_cli.py
```

All commands below assume the shell's current directory is the repo root (`claude-code-toolkit`) unless a step says otherwise.

---

### Task 1: Package scaffolding + usage_fetcher (data source)

**Files:**
- Create: `packages/usage-bar/pyproject.toml`
- Create: `packages/usage-bar/claude_usage_bar/__init__.py`
- Create: `packages/usage-bar/claude_usage_bar/usage_fetcher.py`
- Test: `packages/usage-bar/tests/test_usage_fetcher.py`

**Interfaces:**
- Produces: `UsageSnapshot` dataclass with fields `session_percent: int | None`, `session_reset: str | None`, `week_percent: int | None`, `week_reset: str | None`, `raw_text: str = ""`, `error: str | None = None`, `fatal: bool = False`
- Produces: `parse_usage_text(text: str) -> UsageSnapshot`
- Produces: `fetch_usage(timeout: float = 15.0) -> UsageSnapshot`

- [ ] **Step 1: Create package scaffolding**

Create `packages/usage-bar/pyproject.toml`:

```toml
[project]
name = "claude-usage-bar"
version = "0.1.0"
description = "浮動視窗顯示 Claude Code 的 /usage 額度使用狀況"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7"]

[project.scripts]
claude-usage-bar = "claude_usage_bar.cli:main"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["claude_usage_bar*"]
```

Create `packages/usage-bar/claude_usage_bar/__init__.py` (empty file).

- [ ] **Step 2: Create a venv and install the package in editable/dev mode**

Run:
```bash
cd packages/usage-bar
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
Expected: installs successfully (the package has no importable modules besides the empty `__init__.py` yet — that's fine for an editable install).

- [ ] **Step 3: Write failing tests for `parse_usage_text`**

Create `packages/usage-bar/tests/test_usage_fetcher.py`:

```python
import json
import subprocess
from unittest.mock import patch

import pytest

from claude_usage_bar.usage_fetcher import fetch_usage, parse_usage_text

SAMPLE_FULL = (
    "You are currently using your subscription to power your Claude Code usage\n\n"
    "Current session: 2% used · resets Oct 21, 3:10am (Asia/Taipei)\n"
    "Current week (all models): 3% used · resets Oct 20, 11pm (Asia/Taipei)\n\n"
    "What's contributing to your limits usage?\n"
)

SAMPLE_SESSION_ONLY = (
    "Current session: 45% used · resets Oct 21, 3:10am (Asia/Taipei)\n"
)

SAMPLE_UNPARSEABLE = "Something unexpected happened.\n"


def test_parse_usage_text_full_sample():
    snapshot = parse_usage_text(SAMPLE_FULL)
    assert snapshot.session_percent == 2
    assert snapshot.session_reset == "Oct 21, 3:10am (Asia/Taipei)"
    assert snapshot.week_percent == 3
    assert snapshot.week_reset == "Oct 20, 11pm (Asia/Taipei)"
    assert snapshot.error is None


def test_parse_usage_text_partial_missing_week():
    snapshot = parse_usage_text(SAMPLE_SESSION_ONLY)
    assert snapshot.session_percent == 45
    assert snapshot.week_percent is None
    assert snapshot.error is None


def test_parse_usage_text_unparseable():
    snapshot = parse_usage_text(SAMPLE_UNPARSEABLE)
    assert snapshot.session_percent is None
    assert snapshot.week_percent is None
    assert snapshot.error == "could not parse /usage output"


def test_fetch_usage_success():
    fake_stdout = json.dumps({"result": SAMPLE_FULL})
    fake_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout=fake_stdout, stderr="")
    with patch("claude_usage_bar.usage_fetcher.subprocess.run", return_value=fake_proc) as mock_run:
        snapshot = fetch_usage()
    assert snapshot.session_percent == 2
    assert snapshot.week_percent == 3
    assert snapshot.error is None
    mock_run.assert_called_once_with(
        ["claude", "-p", "/usage", "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=15.0,
        check=False,
    )


def test_fetch_usage_claude_not_found():
    with patch("claude_usage_bar.usage_fetcher.subprocess.run", side_effect=FileNotFoundError):
        snapshot = fetch_usage()
    assert snapshot.fatal is True
    assert snapshot.error == "claude command not found"


def test_fetch_usage_timeout():
    with patch(
        "claude_usage_bar.usage_fetcher.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=15.0),
    ):
        snapshot = fetch_usage()
    assert snapshot.fatal is False
    assert snapshot.error == "request timed out"


def test_fetch_usage_nonzero_exit():
    fake_proc = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
    with patch("claude_usage_bar.usage_fetcher.subprocess.run", return_value=fake_proc):
        snapshot = fetch_usage()
    assert snapshot.fatal is False
    assert "exit code 1" in snapshot.error


def test_fetch_usage_invalid_json():
    fake_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout="not json", stderr="")
    with patch("claude_usage_bar.usage_fetcher.subprocess.run", return_value=fake_proc):
        snapshot = fetch_usage()
    assert snapshot.fatal is False
    assert snapshot.error == "invalid JSON from claude"
```

- [ ] **Step 4: Run tests to verify they fail**

Run:
```bash
cd packages/usage-bar && source .venv/bin/activate
pytest tests/test_usage_fetcher.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'claude_usage_bar.usage_fetcher'` (or `ImportError`).

- [ ] **Step 5: Implement `UsageSnapshot` and `parse_usage_text`**

Create `packages/usage-bar/claude_usage_bar/usage_fetcher.py`:

```python
import json
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

SESSION_RE = re.compile(r"Current session:\s*(\d+)%\s*used\s*·\s*resets\s*([^\n]+)")
WEEK_RE = re.compile(r"Current week \(all models\):\s*(\d+)%\s*used\s*·\s*resets\s*([^\n]+)")


@dataclass
class UsageSnapshot:
    session_percent: Optional[int] = None
    session_reset: Optional[str] = None
    week_percent: Optional[int] = None
    week_reset: Optional[str] = None
    raw_text: str = ""
    error: Optional[str] = None
    fatal: bool = False


def parse_usage_text(text: str) -> UsageSnapshot:
    session_match = SESSION_RE.search(text)
    week_match = WEEK_RE.search(text)

    if not session_match and not week_match:
        return UsageSnapshot(raw_text=text, error="could not parse /usage output")

    snapshot = UsageSnapshot(raw_text=text)
    if session_match:
        snapshot.session_percent = int(session_match.group(1))
        snapshot.session_reset = session_match.group(2).strip()
    if week_match:
        snapshot.week_percent = int(week_match.group(1))
        snapshot.week_reset = week_match.group(2).strip()
    return snapshot


def fetch_usage(timeout: float = 15.0) -> UsageSnapshot:
    try:
        proc = subprocess.run(
            ["claude", "-p", "/usage", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return UsageSnapshot(error="claude command not found", fatal=True)
    except subprocess.TimeoutExpired:
        return UsageSnapshot(error="request timed out")

    if proc.returncode != 0:
        return UsageSnapshot(error=f"claude exited with code {proc.returncode}", raw_text=proc.stdout)

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return UsageSnapshot(error="invalid JSON from claude", raw_text=proc.stdout)

    return parse_usage_text(data.get("result", ""))
```

- [ ] **Step 6: Run tests to verify they pass**

Run:
```bash
pytest tests/test_usage_fetcher.py -v
```
Expected: all 7 tests PASS.

- [ ] **Step 7: Commit**

```bash
cd /userap/hb/git/claude-code-toolkit
git add packages/usage-bar/pyproject.toml packages/usage-bar/claude_usage_bar/__init__.py packages/usage-bar/claude_usage_bar/usage_fetcher.py packages/usage-bar/tests/test_usage_fetcher.py
git commit -m "feat(usage-bar): add usage_fetcher data source + parser"
```

---

### Task 2: UI logic (color/position math + FloatingBar widget)

**Files:**
- Create: `packages/usage-bar/claude_usage_bar/ui.py`
- Test: `packages/usage-bar/tests/test_ui.py`

**Interfaces:**
- Consumes: `UsageSnapshot` from `claude_usage_bar.usage_fetcher` (fields as defined in Task 1)
- Produces: `GREEN`, `YELLOW`, `RED`, `NEUTRAL` color constants (strings)
- Produces: `color_for_percent(percent: int | None) -> str`
- Produces: `compute_position(position: str, window_w: int, window_h: int, screen_w: int, screen_h: int, margin: int = 20) -> tuple[int, int]`
- Produces: `FloatingBar` class with `__init__(self, root: tk.Tk, position: str = "top-right")` and `update_snapshot(self, snapshot: UsageSnapshot) -> None`

- [ ] **Step 1: Write failing tests for the pure logic functions**

Create `packages/usage-bar/tests/test_ui.py`:

```python
import pytest

from claude_usage_bar.ui import GREEN, NEUTRAL, RED, YELLOW, color_for_percent, compute_position


def test_color_for_percent_none_is_neutral():
    assert color_for_percent(None) == NEUTRAL


@pytest.mark.parametrize(
    "percent,expected",
    [
        (0, GREEN),
        (49, GREEN),
        (50, YELLOW),
        (80, YELLOW),
        (81, RED),
        (100, RED),
    ],
)
def test_color_for_percent_thresholds(percent, expected):
    assert color_for_percent(percent) == expected


@pytest.mark.parametrize(
    "position,expected",
    [
        ("top-right", (1800, 20)),
        ("top-left", (20, 20)),
        ("bottom-right", (1800, 1030)),
        ("bottom-left", (20, 1030)),
    ],
)
def test_compute_position(position, expected):
    result = compute_position(
        position, window_w=100, window_h=30, screen_w=1920, screen_h=1080, margin=20
    )
    assert result == expected


def test_compute_position_rejects_unknown_position():
    with pytest.raises(KeyError):
        compute_position("center", window_w=100, window_h=30, screen_w=1920, screen_h=1080)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_ui.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'claude_usage_bar.ui'`.

- [ ] **Step 3: Implement the pure logic functions and `FloatingBar`**

Create `packages/usage-bar/claude_usage_bar/ui.py`:

```python
import tkinter as tk
from tkinter import Menu

from .usage_fetcher import UsageSnapshot

GREEN = "#2ecc71"
YELLOW = "#f1c40f"
RED = "#e74c3c"
NEUTRAL = "#888888"
BG = "#1e1e1e"


def color_for_percent(percent):
    if percent is None:
        return NEUTRAL
    if percent < 50:
        return GREEN
    if percent <= 80:
        return YELLOW
    return RED


def compute_position(position, window_w, window_h, screen_w, screen_h, margin=20):
    positions = {
        "top-right": (screen_w - window_w - margin, margin),
        "top-left": (margin, margin),
        "bottom-right": (screen_w - window_w - margin, screen_h - window_h - margin),
        "bottom-left": (margin, screen_h - window_h - margin),
    }
    return positions[position]


class FloatingBar:
    def __init__(self, root: tk.Tk, position: str = "top-right"):
        self.root = root
        self._position = position
        self._drag_data = {"x": 0, "y": 0}
        self._last_session_percent = None
        self._last_week_percent = None

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.configure(bg=BG)

        self.session_label = tk.Label(
            root, text="Session: --%", fg=NEUTRAL, bg=BG, font=("Sans", 11)
        )
        self.session_label.pack(side="left", padx=(10, 4), pady=6)

        self.week_label = tk.Label(
            root, text="Week: --%", fg=NEUTRAL, bg=BG, font=("Sans", 11)
        )
        self.week_label.pack(side="left", padx=(4, 10), pady=6)

        for widget in (root, self.session_label, self.week_label):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<Button-3>", self._show_context_menu)

        root.bind("<Escape>", lambda event: root.destroy())

        root.update_idletasks()
        self._place_at_default_position()

    def _place_at_default_position(self):
        window_w = self.root.winfo_width()
        window_h = self.root.winfo_height()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x, y = compute_position(self._position, window_w, window_h, screen_w, screen_h)
        self.root.geometry(f"+{x}+{y}")

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x_root - self.root.winfo_x()
        self._drag_data["y"] = event.y_root - self.root.winfo_y()

    def _on_drag_motion(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="結束", command=self.root.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def update_snapshot(self, snapshot: UsageSnapshot) -> None:
        # Keep showing the last known-good percentages across a failed
        # refresh; only append a warning marker, never blank the numbers out.
        if snapshot.session_percent is not None:
            self._last_session_percent = snapshot.session_percent
        if snapshot.week_percent is not None:
            self._last_week_percent = snapshot.week_percent

        warn = " ⚠" if snapshot.error else ""

        session_text = (
            f"Session: {self._last_session_percent}%{warn}"
            if self._last_session_percent is not None
            else f"Session: --%{warn}"
        )
        week_text = (
            f"Week: {self._last_week_percent}%{warn}"
            if self._last_week_percent is not None
            else f"Week: --%{warn}"
        )

        self.session_label.config(text=session_text, fg=color_for_percent(self._last_session_percent))
        self.week_label.config(text=week_text, fg=color_for_percent(self._last_week_percent))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_ui.py -v
```
Expected: all tests PASS. (`FloatingBar` itself has no automated test — it needs a live Tk display, verified manually in Task 4.)

- [ ] **Step 5: Commit**

```bash
cd /userap/hb/git/claude-code-toolkit
git add packages/usage-bar/claude_usage_bar/ui.py packages/usage-bar/tests/test_ui.py
git commit -m "feat(usage-bar): add FloatingBar widget and color/position logic"
```

---

### Task 3: CLI wiring (argparse + thread/queue + entry point)

**Files:**
- Create: `packages/usage-bar/claude_usage_bar/cli.py`
- Test: `packages/usage-bar/tests/test_cli.py`

**Interfaces:**
- Consumes: `fetch_usage` from `claude_usage_bar.usage_fetcher` (Task 1)
- Consumes: `FloatingBar` from `claude_usage_bar.ui` (Task 2)
- Produces: `parse_args(argv: list[str] | None = None) -> argparse.Namespace` with `.interval: int`, `.position: str`
- Produces: `main(argv: list[str] | None = None) -> None` — the `claude-usage-bar` console script entry point

- [ ] **Step 1: Write failing tests for `parse_args`**

Create `packages/usage-bar/tests/test_cli.py`:

```python
import pytest

from claude_usage_bar.cli import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.interval == 60
    assert args.position == "top-right"


def test_parse_args_custom_values():
    args = parse_args(["--interval", "30", "--position", "bottom-left"])
    assert args.interval == 30
    assert args.position == "bottom-left"


def test_parse_args_rejects_invalid_position():
    with pytest.raises(SystemExit):
        parse_args(["--position", "middle"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_cli.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'claude_usage_bar.cli'`.

- [ ] **Step 3: Implement `cli.py`**

Create `packages/usage-bar/claude_usage_bar/cli.py`:

```python
import argparse
import queue
import threading
import tkinter as tk
from tkinter import messagebox

from .ui import FloatingBar
from .usage_fetcher import fetch_usage

POSITIONS = ["top-right", "top-left", "bottom-right", "bottom-left"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="claude-usage-bar",
        description="浮動視窗顯示 Claude Code 的 /usage 額度使用狀況",
    )
    parser.add_argument("--interval", type=int, default=60, help="刷新間隔秒數(預設 60)")
    parser.add_argument(
        "--position", choices=POSITIONS, default="top-right", help="視窗位置(預設 top-right)"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result_queue: "queue.Queue" = queue.Queue()
    stop_event = threading.Event()

    def worker():
        while not stop_event.is_set():
            snapshot = fetch_usage()
            result_queue.put(snapshot)
            if snapshot.fatal:
                return
            stop_event.wait(args.interval)

    root = tk.Tk()
    bar = FloatingBar(root, position=args.position)

    def on_close():
        stop_event.set()
        root.destroy()

    def poll_queue():
        try:
            while True:
                snapshot = result_queue.get_nowait()
                if snapshot.fatal:
                    messagebox.showerror("claude-usage-bar", snapshot.error or "發生無法復原的錯誤")
                    on_close()
                    return
                bar.update_snapshot(snapshot)
        except queue.Empty:
            pass
        root.after(200, poll_queue)

    root.protocol("WM_DELETE_WINDOW", on_close)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    root.after(200, poll_queue)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_cli.py -v
```
Expected: all 3 tests PASS.

- [ ] **Step 5: Re-install editable so the `claude-usage-bar` console script is registered**

Run:
```bash
pip install -e ".[dev]"
```
Expected: installs successfully; `which claude-usage-bar` now points inside `packages/usage-bar/.venv/bin/`.

- [ ] **Step 6: Run the full test suite**

Run:
```bash
pytest -v
```
Expected: all tests across `test_usage_fetcher.py`, `test_ui.py`, `test_cli.py` PASS.

- [ ] **Step 7: Commit**

```bash
cd /userap/hb/git/claude-code-toolkit
git add packages/usage-bar/claude_usage_bar/cli.py packages/usage-bar/tests/test_cli.py
git commit -m "feat(usage-bar): add CLI wiring and claude-usage-bar entry point"
```

---

### Task 4: Package README + manual end-to-end verification

**Files:**
- Create: `packages/usage-bar/README.md`

- [ ] **Step 1: Write the package README**

Create `packages/usage-bar/README.md`:

```markdown
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
```

- [ ] **Step 2: Run the full automated test suite one more time**

Run:
```bash
cd packages/usage-bar && source .venv/bin/activate
pytest -v
```
Expected: all tests PASS.

- [ ] **Step 3: Manually launch and verify the floating bar**

Use the `run` skill (or run directly) to launch the app on the Ubuntu desktop:

```bash
claude-usage-bar
```

Check:
- [ ] A small borderless bar appears near the top-right corner, showing `Session: X% · Week: Y%` with real numbers (not `--%`)
- [ ] Numbers are colored green/yellow/red matching their percentage
- [ ] Dragging the bar with the left mouse button moves it
- [ ] Right-click shows a menu with an option that closes the window; Esc also closes it
- [ ] Launching with `claude-usage-bar --position bottom-left` places it near the bottom-left corner instead
- [ ] (Optional) Temporarily make the `claude` binary unreachable (e.g. `env PATH="$VIRTUAL_ENV/bin:/usr/bin:/bin" claude-usage-bar`, which excludes `~/.local/bin`) and confirm an error dialog appears and the app exits cleanly, instead of hanging or crashing silently
- [ ] (Optional) Simulate one transient failure (e.g. temporarily rename `~/.local/bin/claude` for a single refresh cycle, or run with `--interval 5` and briefly block the binary) and confirm the bar keeps showing the last known percentages with a small `⚠` appended, rather than blanking them out

- [ ] **Step 4: Commit**

```bash
cd /userap/hb/git/claude-code-toolkit
git add packages/usage-bar/README.md
git commit -m "docs(usage-bar): add package README"
```
