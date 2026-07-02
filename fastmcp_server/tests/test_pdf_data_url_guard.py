"""Tests for the embedded-PDF data-URL guard on page create/update tools."""
from __future__ import annotations

import pytest

from fastmcp_server.bookstack.tools_direct_pages import (
    _PDF_DATA_URL_MSG,
    _reject_pdf_data_url,
)

FORBIDDEN = [
    "data:application/pdf;base64,JVBERi0xLjc=",
    "file=data%3Aapplication%2Fpdf%3Bbase64,JVBERi0",
    "data%3Aapplication/pdf%3Bbase64,JVBERi0",
    "data%3Aapplication%2Fpdf%3Bbase64,JVBERi0",
    # Mixed case / encoding still rejected
    "DATA%3AAPPLICATION%2FPDF%3BBASE64,AAAA",
    'src="https://x/pdfjs/web/viewer.html?file=data%3Aapplication%2Fpdf%3Bbase64,AAA"',
]

ALLOWED = [
    "# Just markdown\n\nNo embeds here.",
    'src="https://docs.adium.tech/pdfjs/web/viewer.html?file=%2Fattachments%2F42"',
    "See /attachments/1 for the handbook.",
    "",
]


@pytest.mark.parametrize("content", FORBIDDEN)
def test_rejects_pdf_data_urls(content):
    with pytest.raises(ValueError) as exc:
        _reject_pdf_data_url(content)
    assert str(exc.value) == _PDF_DATA_URL_MSG


@pytest.mark.parametrize("content", ALLOWED)
def test_allows_attachment_and_plain_content(content):
    _reject_pdf_data_url(content)  # must not raise


def test_error_message_is_exact():
    assert _PDF_DATA_URL_MSG == (
        "Refusing to update BookStack page with embedded PDF data URL. "
        "Upload the PDF as a BookStack attachment and embed /attachments/{id} instead."
    )
