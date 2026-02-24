import base64


def decode_graph_attachment(content_bytes: str) -> bytes:
    """Decode Graph attachment contentBytes (base64 string) into raw bytes."""
    if not content_bytes:
        return b""
    try:
        return base64.b64decode(content_bytes, validate=True)
    except Exception:
        # Some payloads can include non-base64 chars/newlines.
        return base64.b64decode(content_bytes)
