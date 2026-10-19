import pytest
from pydantic import ValidationError

from app.schemas.source import ParsedShape, ShapeType, SourceAnchor


def _anchor() -> SourceAnchor:
    return SourceAnchor(
        document_id="doc_01",
        filename="source.pptx",
        page=1,
        shape_id="shape_1",
        text_quote="635亿条",
    )


def test_parsed_shape_accepts_valid_geometry() -> None:
    shape = ParsedShape(
        shape_id="shape_1",
        shape_type=ShapeType.TEXT_BOX,
        text="635亿条",
        x=0.5,
        y=1.0,
        w=3.0,
        h=1.0,
        source_anchor=_anchor(),
    )

    assert shape.shape_type == ShapeType.TEXT_BOX


def test_parsed_shape_rejects_negative_width() -> None:
    with pytest.raises(ValidationError):
        ParsedShape(
            shape_id="shape_1",
            shape_type=ShapeType.TEXT_BOX,
            text="635亿条",
            x=0.5,
            y=1.0,
            w=-1.0,
            h=1.0,
            source_anchor=_anchor(),
        )
