from pathlib import Path

import pytest

from app.services.parser_errors import ParserError
from app.services.parsers.parser_service import parse_source_document


def test_parse_source_document_rejects_unsupported_suffix(tmp_path: Path) -> None:
    path = tmp_path / "source.ppt"
    path.write_bytes(b"test")

    with pytest.raises(ParserError) as exc_info:
        parse_source_document(
            path,
            document_id="doc_01",
            extracted_text_path="jobs/job_1/parsed/doc_01.json",
        )

    assert exc_info.value.code == "UNSUPPORTED_FILE_TYPE"


def test_parse_source_document_rejects_signature_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "supplement.pdf"
    path.write_bytes(b"PK\x03\x04 not a pdf")

    with pytest.raises(ParserError) as exc_info:
        parse_source_document(
            path,
            document_id="doc_01",
            extracted_text_path="jobs/job_1/parsed/doc_01.json",
        )

    assert exc_info.value.code == "UNSUPPORTED_FILE_TYPE"
