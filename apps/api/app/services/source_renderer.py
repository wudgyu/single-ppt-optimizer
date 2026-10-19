"""Isolated source PPTX page rendering service."""

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image

from app.schemas.source import SourceFileType
from app.services.file_validation import validate_document_file
from app.services.parser_errors import ParserError


@dataclass(frozen=True)
class SourceRenderConfig:
    libreoffice_bin: str = "libreoffice"
    pdftoppm_bin: str = "pdftoppm"
    dpi: int = 150
    timeout_seconds: int = 90
    retries: int = 1


@dataclass(frozen=True)
class SourcePageRenderResult:
    artifact_id: str
    storage_key: str
    sha256: str
    page: int
    width: int
    height: int
    size_bytes: int


class SourceSlideRenderer:
    def __init__(self, config: SourceRenderConfig | None = None) -> None:
        self.config = config or SourceRenderConfig()

    def render(self, pptx_path: Path, output_dir: Path, page: int) -> SourcePageRenderResult:
        if page < 1:
            raise ParserError(
                "TARGET_SLIDE_OUT_OF_RANGE",
                "Target slide must be positive.",
                details={"target_slide": page},
            )
        validate_document_file(pptx_path, SourceFileType.PPTX)
        output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="source-render-", dir=output_dir) as temp_dir:
            temp_path = Path(temp_dir)
            pdf_path = self._convert_to_pdf(pptx_path, temp_path)
            self._validate_target_page(pdf_path, page)
            png_path = self._extract_page_png(pdf_path, temp_path, page)
            return self._save_artifact(png_path, output_dir, page)

    def _convert_to_pdf(self, pptx_path: Path, temp_path: Path) -> Path:
        command = [
            self.config.libreoffice_bin,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(temp_path),
            str(pptx_path),
        ]
        last_timeout: subprocess.TimeoutExpired | None = None
        for _ in range(self.config.retries + 1):
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    timeout=self.config.timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                last_timeout = exc
                continue

            if completed.returncode != 0:
                raise ParserError(
                    "RENDER_FAILED",
                    "LibreOffice could not convert the source file.",
                    details={"returncode": completed.returncode},
                )
            pdf_candidates = list(temp_path.glob("*.pdf"))
            if not pdf_candidates:
                raise ParserError(
                    "RENDER_FAILED",
                    "LibreOffice did not produce a PDF.",
                    details={"filename": pptx_path.name},
                )
            return pdf_candidates[0]

        raise ParserError(
            "RENDER_FAILED",
            "LibreOffice rendering timed out.",
            details={"timeout_seconds": self.config.timeout_seconds},
        ) from last_timeout

    def _validate_target_page(self, pdf_path: Path, page: int) -> None:
        try:
            with fitz.open(str(pdf_path)) as document:
                page_count = document.page_count
        except Exception as exc:
            raise ParserError(
                "RENDER_FAILED",
                "Rendered PDF could not be opened.",
                details={"filename": pdf_path.name},
            ) from exc
        if not 1 <= page <= page_count:
            raise ParserError(
                "TARGET_SLIDE_OUT_OF_RANGE",
                "Target slide is outside the rendered document.",
                details={"target_slide": page, "page_count": page_count},
            )

    def _extract_page_png(self, pdf_path: Path, temp_path: Path, page: int) -> Path:
        prefix = temp_path / f"page-{page}"
        command = [
            self.config.pdftoppm_bin,
            "-png",
            "-r",
            str(self.config.dpi),
            "-f",
            str(page),
            "-l",
            str(page),
            str(pdf_path),
            str(prefix),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                timeout=self.config.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ParserError(
                "RENDER_FAILED",
                "PNG extraction timed out.",
                details={"timeout_seconds": self.config.timeout_seconds},
            ) from exc
        if completed.returncode != 0:
            raise ParserError(
                "RENDER_FAILED",
                "PNG extraction failed.",
                details={"returncode": completed.returncode},
            )
        png_candidates = list(temp_path.glob(f"page-{page}-*.png"))
        if not png_candidates:
            raise ParserError(
                "RENDER_FAILED",
                "PNG extraction did not produce an image.",
                details={"page": page},
            )
        return png_candidates[0]

    def _save_artifact(self, png_path: Path, output_dir: Path, page: int) -> SourcePageRenderResult:
        try:
            with Image.open(png_path) as image:
                width, height = image.size
                image.verify()
        except Exception as exc:
            raise ParserError(
                "RENDER_FAILED",
                "Rendered source page is not a valid image.",
                details={"page": page},
            ) from exc
        if width <= 0 or height <= 0 or png_path.stat().st_size == 0:
            raise ParserError(
                "RENDER_FAILED",
                "Rendered source page is empty.",
                details={"page": page},
            )

        artifact_dir = output_dir / "rendered_source"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"source_page_{page}.png"
        shutil.copyfile(png_path, artifact_path)
        payload = artifact_path.read_bytes()

        return SourcePageRenderResult(
            artifact_id=f"art_source_p{page}",
            storage_key=artifact_path.relative_to(output_dir).as_posix(),
            sha256=hashlib.sha256(payload).hexdigest(),
            page=page,
            width=width,
            height=height,
            size_bytes=len(payload),
        )
