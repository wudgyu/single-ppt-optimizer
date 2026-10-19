from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

from app.services.parser_errors import ParserError
from app.services.source_renderer import SourceRenderConfig, SourceSlideRenderer


def _write_png(path: Path) -> None:
    with Image.new("RGB", (2, 3), color=(7, 17, 43)) as image:
        image.save(path)


def _fake_fitz_open(pages: int) -> Any:
    @contextmanager
    def open_document(path: str) -> Iterator[Any]:
        yield SimpleNamespace(page_count=pages)

    return open_document


def test_render_rejects_non_positive_page(tmp_path: Path) -> None:
    renderer = SourceSlideRenderer()

    with pytest.raises(ParserError) as exc_info:
        renderer.render(tmp_path / "source.pptx", tmp_path, 0)

    assert exc_info.value.code == "TARGET_SLIDE_OUT_OF_RANGE"


def test_render_saves_and_validates_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.pptx"
    source.write_bytes(b"PK\x03\x04 placeholder")
    output_dir = tmp_path / "job"
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        if "--convert-to" in command:
            pdf_path = Path(command[-2]) / "source.pdf"
            pdf_path.write_bytes(b"%PDF-1.7\n")
        else:
            png_path = Path(str(command[-1]) + "-1.png")
            _write_png(png_path)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("app.services.source_renderer.subprocess.run", fake_run)
    monkeypatch.setattr(
        "app.services.source_renderer.fitz.open",
        _fake_fitz_open(1),
    )
    renderer = SourceSlideRenderer(SourceRenderConfig(timeout_seconds=1))

    result = renderer.render(source, output_dir, 1)

    artifact = output_dir / result.storage_key
    assert artifact.is_file()
    assert artifact.stat().st_size == result.size_bytes
    assert result.width == 2
    assert result.height == 3
    assert len(result.sha256) == 64
    assert len(calls) == 2
