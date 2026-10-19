import pytest

from app.schemas.source import (
    FactLedger,
    FactStatus,
    FactType,
    SourceAnchor,
    SourceFact,
)
from app.services.conflict_detection import detect_conflicts
from app.services.fact_revision import validate_fact_revision
from app.services.number_normalization import normalize_number


def _anchor(shape_id: str = "shape_1") -> SourceAnchor:
    return SourceAnchor(
        document_id="doc_01",
        filename="source.pptx",
        page=1,
        shape_id=shape_id,
        text_quote="635亿条",
    )


def _fact(
    fact_id: str,
    value: float,
    *,
    entity: str | None = "温州数安港",
    qualifier: str | None = "归集数据规模",
    unit: str = "条",
    status: FactStatus = FactStatus.VERIFIED,
    conflict_group_id: str | None = None,
) -> SourceFact:
    return SourceFact(
        fact_id=fact_id,
        statement=f"{entity or 'unknown'} {qualifier or 'unknown'} {value}",
        value_raw=str(value),
        value_normalized=value,
        unit=unit,
        entity=entity,
        qualifier=qualifier,
        source=_anchor(),
        confidence=0.98,
        fact_type=FactType.SOURCE_FACT,
        status=status,
        conflict_group_id=conflict_group_id,
    )


@pytest.mark.parametrize(
    ("raw", "expected", "unit"),
    [
        ("635亿条", 63_500_000_000, "条"),
        ("12.5万条", 125_000, "条"),
        ("1.2万亿条", 1_200_000_000_000, "条"),
        ("63,500,000,000条", 63_500_000_000, "条"),
        ("45%", 45, "%"),
    ],
)
def test_normalize_number(raw: str, expected: float, unit: str) -> None:
    normalized = normalize_number(raw)

    assert normalized is not None
    assert normalized.value_raw == raw
    assert normalized.value_normalized == expected
    assert normalized.unit == unit


def test_normalize_number_rejects_non_numeric_text() -> None:
    assert normalize_number("无可用数字") is None


def test_detect_conflicts_groups_same_entity_and_qualifier() -> None:
    ledger = FactLedger(
        facts=[
            _fact("F001", 635_000_000_000),
            _fact("F002", 500_000_000_000),
            _fact("F003", 100, qualifier="场景数量"),
        ]
    )

    result = detect_conflicts(ledger)

    assert len(result.conflicts) == 1
    assert result.conflicts[0].fact_ids == ["F001", "F002"]
    assert all(fact.status == FactStatus.CONFLICT for fact in result.facts[:2])
    assert result.facts[2].status == FactStatus.VERIFIED


def test_detect_conflicts_ignores_equal_normalized_values() -> None:
    ledger = FactLedger(
        facts=[
            _fact("F001", 635_000_000_000),
            _fact("F002", 635_000_000_000),
        ]
    )

    result = detect_conflicts(ledger)

    assert result.conflicts == []
    assert all(fact.status == FactStatus.VERIFIED for fact in result.facts)


def test_validate_fact_revision_accepts_unchanged_fact() -> None:
    ledger = FactLedger(facts=[_fact("F001", 635_000_000_000)])
    revision = _fact("F001", 635_000_000_000)

    validate_fact_revision(revision, ledger)


def test_validate_fact_revision_requires_human_review_for_conflict() -> None:
    ledger = FactLedger(
        facts=[
            _fact(
                "F001",
                635_000_000_000,
                status=FactStatus.CONFLICT,
                conflict_group_id="CONFLICT-001",
            )
        ]
    )

    with pytest.raises(Exception, match="human review"):
        validate_fact_revision(_fact("F001", 500_000_000_000), ledger)
