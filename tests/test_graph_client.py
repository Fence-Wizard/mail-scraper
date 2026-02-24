from mail_scraper.graph_client import GraphClient


def test_normalize_graph_path_absolute_next_link() -> None:
    absolute = "https://graph.microsoft.com/v1.0/users/abc/messages?$skip=50"
    normalized = GraphClient._normalize_graph_path(absolute)
    assert normalized == "/users/abc/messages?$skip=50"


def test_normalize_graph_path_relative_path() -> None:
    relative = "/users/abc/mailFolders"
    normalized = GraphClient._normalize_graph_path(relative)
    assert normalized == relative
