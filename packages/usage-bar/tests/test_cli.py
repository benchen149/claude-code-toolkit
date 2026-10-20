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


def test_parse_args_rejects_non_positive_interval():
    with pytest.raises(SystemExit):
        parse_args(["--interval", "0"])
