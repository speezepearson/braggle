from bridge.server import CLIENT_HTML

def test_client_html_exists():
    assert CLIENT_HTML.is_file()
