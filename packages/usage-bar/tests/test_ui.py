import pytest

from claude_usage_bar.ui import (
    GREEN,
    NEUTRAL,
    RED,
    YELLOW,
    color_for_percent,
    compute_position,
    format_bar_text,
    format_reset_text,
)


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


def test_format_bar_text_good_values_no_error():
    session_text, week_text = format_bar_text(2, 3, has_error=False)
    assert session_text == "Session: 2%"
    assert week_text == "Week: 3%"


def test_format_bar_text_keeps_old_values_on_error():
    session_text, week_text = format_bar_text(2, 3, has_error=True)
    assert session_text == "Session: 2% ⚠"
    assert week_text == "Week: 3%"


def test_format_bar_text_cold_start_with_error():
    session_text, week_text = format_bar_text(None, None, has_error=True)
    assert session_text == "Session: --% ⚠"
    assert week_text == "Week: --%"


def test_format_reset_text_with_values():
    session_reset, week_reset = format_reset_text(
        "Oct 21, 3:10am (Asia/Taipei)", "Oct 27, 11pm (Asia/Taipei)"
    )
    assert session_reset == "resets Oct 21, 3:10am (Asia/Taipei)"
    assert week_reset == "resets Oct 27, 11pm (Asia/Taipei)"


def test_format_reset_text_no_values_yet():
    session_reset, week_reset = format_reset_text(None, None)
    assert session_reset == ""
    assert week_reset == ""


def test_format_reset_text_partial():
    session_reset, week_reset = format_reset_text("Oct 21, 3:10am (Asia/Taipei)", None)
    assert session_reset == "resets Oct 21, 3:10am (Asia/Taipei)"
    assert week_reset == ""
