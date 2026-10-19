"""FactLedger extraction and source-reference validation."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.schemas.source import (
    FactLedger,
    SourceAnchor,
    SourceDocument,
)
from app.services.llm import StructuredFactAdapter
from app.services.parser_errors import ParserError


@dataclass(frozen=True)
class FactCandidate:
    anchor: SourceAnchor
    text: str


@dataclass(frozen=True)
class FactService:
    adapter: StructuredFactAdapter

    @staticmethod
    def _anchor_key(anchor: SourceAnchor) -> tuple[object, ...]:
        return (
            anchor.document_id,
            anchor.filename,
            anchor.page,
            anchor.paragraph_index,
            anchor.shape_id,
            anchor.table_id,
            anchor.chart_id,
        )

    def prepare_candidates(self, documents: Sequence[SourceDocument]) -> list[FactCandidate]:
        candidates: list[FactCandidate] = []
        for document in documents:
            for slide in document.parsed_slides:
                for shape in slide.shapes:
                    candidates.append(FactCandidate(shape.source_anchor, shape.text))
                    for table in shape.tables:
                        table_text = "\n".join(cell.text for cell in table.cells)
                        candidates.append(FactCandidate(table.source_anchor, table_text))
                    for chart in shape.charts:
                        chart_text = "\n".join(
                            [chart.chart_id, *chart.categories]
                            + [f"{series.name}: {series.values}" for series in chart.series]
                        )
                        candidates.append(FactCandidate(chart.source_anchor, chart_text))
            for block in document.parsed_blocks:
                text = block.text
                if block.table:
                    text = "\n".join(cell.text for cell in block.table.cells)
                candidates.append(FactCandidate(block.source_anchor, text))
        return candidates

    def build_prompt(self, documents: Sequence[SourceDocument]) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "fact_extraction_v1.md"
        candidates = self.prepare_candidates(documents)
        rendered_candidates = "\n".join(
            f"- document_id={candidate.anchor.document_id}; "
            f"page={candidate.anchor.page}; "
            f"paragraph_index={candidate.anchor.paragraph_index}; "
            f"shape_id={candidate.anchor.shape_id}; "
            f"table_id={candidate.anchor.table_id}; "
            f"chart_id={candidate.anchor.chart_id}; "
            f"text={candidate.text!r}"
            for candidate in candidates
        )
        return f"{prompt_path.read_text(encoding='utf-8')}\n\nCANDIDATES:\n{rendered_candidates}"

    def extract_fact_ledger(self, documents: Sequence[SourceDocument]) -> FactLedger:
        candidates = self.prepare_candidates(documents)
        if not candidates:
            return FactLedger()

        candidate_keys = {self._anchor_key(candidate.anchor) for candidate in candidates}
        prompt = self.build_prompt(documents)
        ledger = self.adapter.extract_fact_ledger(prompt)

        for fact in ledger.facts:
            if self._anchor_key(fact.source) not in candidate_keys:
                raise ParserError(
                    "MODEL_SCHEMA_INVALID",
                    "Model output referenced a source anchor that was not supplied.",
                    details={"fact_id": fact.fact_id},
                )
        return ledger
