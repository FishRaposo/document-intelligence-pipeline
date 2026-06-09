from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_redis():
    mock = MagicMock()
    mock.ping.return_value = True
    return mock


@pytest.fixture
def sample_txt_bytes():
    return b"This is a sample text document.\nIt has multiple lines.\n\nAnd a blank line."


@pytest.fixture
def sample_md_bytes():
    return b"# Heading One\n\nThis is **bold** and *italic* text.\n\n- list item 1\n- list item 2\n\n[Link text](http://example.com)\n\n> A blockquote\n\n`inline code`"


@pytest.fixture
def sample_html_bytes():
    return b"<html><head><title>Test</title></head><body><h1>Title</h1><p>Paragraph text here.</p><script>console.log('x')</script></body></html>"


@pytest.fixture
def sample_pdf_bytes():
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"


@pytest.fixture
def sample_docx_bytes():
    return b"PK\x03\x04\x14\x00\x06\x00"


@pytest.fixture
def sample_chunks():
    return [
        {"chunk_id": 0, "content": "first chunk", "word_count": 2},
        {"chunk_id": 1, "content": "second chunk", "word_count": 2},
    ]
