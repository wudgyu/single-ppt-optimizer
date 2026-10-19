"""Validation for revised or derived facts."""

from app.schemas.source import FactLedger, SourceFact
from app.services.parser_errors import ParserError


def validate_fact_revision(
    revision: SourceFact,
    ledger: FactLedger,
    *,
    allow_conflict_selection: bool = False,
) -> None:
    facts_by_id = {fact.fact_id: fact for fact in ledger.facts}
    original = facts_by_id.get(revision.fact_id)
    if original is None:
        raise ParserError(
            "MODEL_SCHEMA_INVALID",
            "Revised fact references an unknown source fact ID.",
            details={"fact_id": revision.fact_id},
        )

    for input_fact_id in revision.input_fact_ids:
        if input_fact_id not in facts_by_id:
            raise ParserError(
                "MODEL_SCHEMA_INVALID",
                "Derived fact references an unknown input fact ID.",
                details={"fact_id": revision.fact_id, "input_fact_id": input_fact_id},
            )

    if original.conflict_group_id and not allow_conflict_selection:
        raise ParserError(
            "FACT_CONFLICT_REQUIRES_REVIEW",
            "A conflicting fact cannot be revised without human review.",
            details={"fact_id": revision.fact_id},
        )

    changed_value_fields = any(
        getattr(revision, field) != getattr(original, field)
        for field in (
            "value_raw",
            "value_normalized",
            "unit",
            "entity",
            "qualifier",
            "time_scope",
        )
    )
    if changed_value_fields and not allow_conflict_selection:
        raise ParserError(
            "FACT_CONFLICT_REQUIRES_REVIEW",
            "Changing fact values requires explicit human review.",
            details={"fact_id": revision.fact_id},
        )
