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
