from collections.abc import Mapping
from typing import Any

import pytest

from app.schemas.source import (
    FactStatus,
    FactType,
    ParsedShape,
    ParsedSlide,
    ShapeType,
    SourceAnchor,
    SourceDocument,
    SourceFileType,
)
from app.services.fact_service import FactService
from app.services.llm import ModelClientError, StructuredFactAdapter
from app.services.parser_errors import ParserError


def _anchor(shape_id: str = "shape_1") -> SourceAnchor:
    return SourceAnchor(
        document_id="doc_01",
        filename="source.pptx",
        page=1,
        shape_id=shape_id,
        text_quote="温州数安港归集635亿条",
    )


def _document() -> SourceDocument:
    shape = ParsedShape(
        shape_id="shape_1",
        shape_type=ShapeType.TEXT_BOX,
        text="温州数安港归集635亿条",
        source_anchor=_anchor(),
    )
    slide = ParsedSlide(
        slide_number=1,
        canvas_width_inches=13.333,
        canvas_height_inches=7.5,
        background="unknown",
        shapes=[shape],
    )
    return SourceDocument(
        document_id="doc_01",
        filename="source.pptx",
        file_type=SourceFileType.PPTX,
        sha256="a" * 64,
        page_count=1,
        extracted_text_path="jobs/job_1/parsed/doc_01.json",
        parsed_slides=[slide],
    )


def _valid_payload() -> dict[str, Any]:
    return {
        "facts": [
            {
                "fact_id": "F001",
                "statement": "温州数安港归集数据规模为635亿条",
                "value_raw": "635亿条",
                "value_normalized": 63500000000,
                "unit": "条",
                "entity": "温州数安港",
                "source": _anchor().model_dump(),
                "confidence": 0.98,
                "fact_type": FactType.SOURCE_FACT,
                "status": FactStatus.VERIFIED,
            }
        ]
    }


class FakeModelClient:
    last_usage: dict[str, int] | None

    def __init__(self, responses: list[Mapping[str, Any] | Exception]) -> None:
        self.responses = responses
        self.calls = 0
        self.last_usage = None

    def complete_json(self, prompt: str) -> Mapping[str, Any]:
        self.calls += 1
        response = self.responses[min(self.calls - 1, len(self.responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return response


def test_fact_service_returns_validated_ledger() -> None:
    client = FakeModelClient([_valid_payload()])
    service = FactService(StructuredFactAdapter(client, model_name="test-model", max_retries=0))

    ledger = service.extract_fact_ledger([_document()])

    assert len(ledger.facts) == 1
    assert ledger.facts[0].fact_id == "F001"
    assert service.prepare_candidates([_document()])[0].text == "温州数安港归集635亿条"


def test_fact_service_rejects_invented_anchor() -> None:
    payload = _valid_payload()
    payload["facts"][0]["source"] = _anchor("shape_missing").model_dump()
    client = FakeModelClient([payload])
    service = FactService(StructuredFactAdapter(client, model_name="test-model", max_retries=0))

    with pytest.raises(ParserError) as exc_info:
        service.extract_fact_ledger([_document()])

    assert exc_info.value.code == "MODEL_SCHEMA_INVALID"


def test_adapter_retries_malformed_json_then_fails() -> None:
    client = FakeModelClient([{"unexpected": True}, {"unexpected": True}])
    adapter = StructuredFactAdapter(client, model_name="test-model", max_retries=1)

    with pytest.raises(ModelClientError):
        adapter.extract_fact_ledger("prompt")

    assert client.calls == 2


def test_adapter_retries_timeout_then_records_usage() -> None:
    client = FakeModelClient([TimeoutError(), _valid_payload()])
    client.last_usage = {"prompt_tokens": 10, "completion_tokens": 20}
    adapter = StructuredFactAdapter(client, model_name="test-model", max_retries=1)

    ledger = adapter.extract_fact_ledger("prompt")

    assert len(ledger.facts) == 1
    assert client.calls == 2
    assert adapter.last_usage == {
        "prompt_tokens": 10,
        "completion_tokens": 20,
    }
