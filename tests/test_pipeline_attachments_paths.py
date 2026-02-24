from pathlib import Path

from mail_scraper.pipeline_attachments import _make_attachment_filename, _make_message_dir


def test_make_message_dir_is_short_and_stable() -> None:
    output_root = Path("raw_data")
    mailbox_key = "tmyers_at_hurricanefence.com"
    graph_id = "AAMkADM0M2IzMTA4LWJlNmQtNDc1ZS05YmUyLTExOTdjNmJkMzA5OQBGAAAAAACz3y1Ld4rGRqR_Xaprb-ns"

    one = _make_message_dir(output_root, mailbox_key, 12345, graph_id)
    two = _make_message_dir(output_root, mailbox_key, 12345, graph_id)

    assert one == two
    assert one.name.startswith("m12345_")
    assert len(one.name) <= 24


def test_make_attachment_filename_sanitizes_and_bounds_length() -> None:
    original = 'Price:Quote*for/Job?<123>.pdf'
    attachment_id = "AAMkAD-attachment-id-example"

    safe = _make_attachment_filename(original, attachment_id, max_len=80)

    assert ":" not in safe
    assert "/" not in safe
    assert "*" not in safe
    assert "?" not in safe
    assert "<" not in safe
    assert ">" not in safe
    assert safe.endswith(".pdf")
    assert len(safe) <= 80
