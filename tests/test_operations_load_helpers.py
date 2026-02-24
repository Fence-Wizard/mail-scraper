from mail_scraper.operations import _canonicalize_vendor, _clean_text, _parse_money


def test_clean_text_normalizes_empty_and_nan() -> None:
    assert _clean_text("  hello  ") == "hello"
    assert _clean_text("nan") is None
    assert _clean_text("") is None


def test_parse_money_handles_currency_commas() -> None:
    assert _parse_money("$12,345.67") == 12345.67
    assert _parse_money(" 98.10 ") == 98.1
    assert _parse_money(None) is None


def test_canonicalize_vendor() -> None:
    assert _canonicalize_vendor("Hurricane Fence Co., VA") == "hurricane fence co va"
