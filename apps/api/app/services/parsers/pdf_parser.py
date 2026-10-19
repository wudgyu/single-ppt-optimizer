"""Searchable PDF parser service."""

import hashlib
from pathlib import Path

import fitz

from app.schemas.source import (
    ParsedBlock,
    SourceAnchor,
    SourceDocument,
    SourceFileType,
)
from app.services.file_validation import validate_document_file
from app.services.parser_errors import ParserError


def parse_pdf(
    path: Path,
    *,
    document_id: str,
    filename: str,
    extracted_text_path: str,
    max_size_bytes: int = 100 * 1024 * 1024,
    max_pages: int = 100,
) -> SourceDocument:
    validate_document_file(path, SourceFileType.PDF, max_size_bytes=max_size_bytes)
    try:
        document = fitz.open(str(path))
    except Exception as exc:
        raise ParserError(
            "CORRUPTED_FILE",
            "PDF file could not be opened.",
            details={"filename": filename},
        ) from exc

    page_count = document.page_count
    if page_count == 0:
        document.close()
        raise ParserError(
            "CORRUPTED_FILE", "PDF file has no pages.", details={"filename": filename}
        )
    if page_count > max_pages:
        document.close()
        raise ParserError(
            "FILE_TOO_LARGE",
            "PDF page count exceeds the configured limit.",
            details={"page_count": page_count, "max_pages": max_pages},
        )

    blocks: list[ParsedBlock] = []
    image_only_pages: list[int] = []
    for page_index in range(page_count):
        page = document.load_page(page_index)
        page_number = page_index + 1
        raw_blocks = page.get_text("blocks")
        text_blocks = [block for block in raw_blocks if block[6] == 0 and str(block[4]).strip()]
        if not text_blocks:
            image_only_pages.append(page_number)
            continue

        for raw_block in text_blocks:
            block_number = int(raw_block[5])
            text = str(raw_block[4]).strip()
            blocks.append(
                ParsedBlock(
                    block_id=f"pdf_p{page_number}_b{block_number}",
                    block_type="text",
                    text=text,
                    page=page_number,
                    paragraph_index=block_number,
                    source_anchor=SourceAnchor(
                        document_id=document_id,
                        filename=filename,
                        page=page_number,
                        paragraph_index=block_number,
                        text_quote=text[:500],
                    ),
                )
            )
    document.close()

    return SourceDocument(
        document_id=document_id,
        filename=filename,
        file_type=SourceFileType.PDF,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        page_count=page_count,
        extracted_text_path=extracted_text_path,
        parsed_blocks=blocks,
        image_only_pages=image_only_pages,
    )


def render_pdf_pages(
    path: Path,
    output_dir: Path,
    *,
    dpi: int = 150,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        document = fitz.open(str(path))
    except Exception as exc:
        raise ParserError(
            "CORRUPTED_FILE",
            "PDF file could not be opened.",
            details={"filename": path.name},
        ) from exc

    rendered: list[Path] = []
    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(dpi=dpi)
        destination = output_dir / f"source_page_{page_index + 1}.png"
        pixmap.save(str(destination))
        rendered.append(destination)
    document.close()
    return rendered
