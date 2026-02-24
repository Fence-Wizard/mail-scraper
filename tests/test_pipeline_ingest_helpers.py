from datetime import datetime, timezone

from mail_scraper.pipeline_ingest import _path_matches, _to_dt


def test_to_dt_iso8601() -> None:
    parsed = _to_dt("2026-02-23T12:34:56Z")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.year == 2026


def test_path_matches_include_exclude() -> None:
    path = ["msgfolderroot", "Finance", "Invoices"]
    assert _path_matches(path, ["finance"], [])
    assert not _path_matches(path, ["sales"], [])
    assert not _path_matches(path, [], ["invoices"])
    assert _path_matches(path, [], [])
