"""File boundary validation used before document parsing."""

from pathlib import Path

from app.schemas.source import SourceFileType
from app.services.parser_errors import ParserError

MAGIC_PREFIXES: dict[SourceFileType, bytes] = {
    SourceFileType.PPTX: b"PK\x03\x04",
    SourceFileType.DOCX: b"PK\x03\x04",
    SourceFileType.PDF: b"%PDF-",
}


def validate_document_file(
    path: Path,
    file_type: SourceFileType,
    *,
    max_size_bytes: int = 100 * 1024 * 1024,
) -> None:
    if not path.is_file():
        raise ParserError(
            "CORRUPTED_FILE",
            "Source file does not exist.",
            details={"path": str(path)},
        )

    size = path.stat().st_size
    if size == 0:
        raise ParserError("CORRUPTED_FILE", "Source file is empty.", details={"path": str(path)})
    if size > max_size_bytes:
        raise ParserError(
            "FILE_TOO_LARGE",
            "Source file exceeds the configured limit.",
            details={"size_bytes": size, "max_size_bytes": max_size_bytes},
        )

    with path.open("rb") as stream:
        prefix = stream.read(8)
    if not prefix.startswith(MAGIC_PREFIXES[file_type]):
        raise ParserError(
            "UNSUPPORTED_FILE_TYPE",
            "Source file signature does not match its extension.",
            details={"filename": path.name, "expected_type": str(file_type)},
        )
