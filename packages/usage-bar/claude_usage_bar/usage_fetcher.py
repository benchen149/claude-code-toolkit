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
    elif week_match:
        # No session line alongside a week line means no active 5-hour
        # window. Empty reset (not None) clears any stale reset time in the UI.
        snapshot.session_percent = 0
        snapshot.session_reset = ""
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
        return UsageSnapshot(
            error=f"claude failed, exit code {proc.returncode}",
            raw_text=f"{proc.stdout}\n{proc.stderr}".strip(),
        )

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return UsageSnapshot(
            error="invalid JSON from claude",
            raw_text=f"{proc.stdout}\n{proc.stderr}".strip(),
        )

    return parse_usage_text(data.get("result", ""))
