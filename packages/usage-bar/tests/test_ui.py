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
