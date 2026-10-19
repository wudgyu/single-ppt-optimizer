"""Registered document parser boundary."""

from pathlib import Path

from app.schemas.source import SourceDocument, SourceFileType
from app.services.parser_errors import ParserError
from app.services.parsers.docx_parser import parse_docx
from app.services.parsers.pdf_parser import parse_pdf
from app.services.parsers.pptx_parser import parse_pptx


def parse_source_document(
    path: Path,
    *,
    document_id: str,
    extracted_text_path: str,
    max_size_bytes: int = 100 * 1024 * 1024,
    target_slide: int | None = None,
) -> SourceDocument:
    suffix = path.suffix.lower()
    file_type_by_suffix = {
        ".pptx": SourceFileType.PPTX,
        ".docx": SourceFileType.DOCX,
        ".pdf": SourceFileType.PDF,
    }
    file_type = file_type_by_suffix.get(suffix)
    if file_type is None:
        raise ParserError(
            "UNSUPPORTED_FILE_TYPE",
            "Document file type is not supported.",
            details={"filename": path.name, "suffix": suffix},
        )

    if file_type == SourceFileType.PPTX:
        return parse_pptx(
            path,
            document_id=document_id,
            filename=path.name,
            extracted_text_path=extracted_text_path,
            max_size_bytes=max_size_bytes,
            target_slide=target_slide,
        )
    if file_type == SourceFileType.DOCX:
        return parse_docx(
            path,
            document_id=document_id,
            filename=path.name,
            extracted_text_path=extracted_text_path,
            max_size_bytes=max_size_bytes,
        )
    return parse_pdf(
        path,
        document_id=document_id,
        filename=path.name,
        extracted_text_path=extracted_text_path,
        max_size_bytes=max_size_bytes,
    )
