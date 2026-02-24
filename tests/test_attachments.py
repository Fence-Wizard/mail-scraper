import base64

from mail_scraper.attachments import decode_graph_attachment


def test_decode_graph_attachment_round_trip() -> None:
    payload = b"sample-binary-\x00-\xff"
    encoded = base64.b64encode(payload).decode("ascii")

    decoded = decode_graph_attachment(encoded)

    assert decoded == payload


def test_decode_graph_attachment_empty() -> None:
    assert decode_graph_attachment("") == b""
