"""Conflict grouping for normalized source facts."""

from collections import defaultdict

from app.schemas.source import ConflictGroup, FactLedger, FactStatus


def detect_conflicts(ledger: FactLedger) -> FactLedger:
    candidates: dict[tuple[str | None, str | None, str | None], list[int]] = defaultdict(list)
    for index, fact in enumerate(ledger.facts):
        if fact.entity is None or fact.value_normalized is None:
            continue
        key = (fact.entity, fact.qualifier, fact.time_scope)
        candidates[key].append(index)

    conflicts: list[ConflictGroup] = []
    facts = [fact.model_copy(deep=True) for fact in ledger.facts]
    group_number = 1
    for indexes in candidates.values():
        values = {
            facts[index].value_normalized
            for index in indexes
            if facts[index].value_normalized is not None
        }
        if len(values) <= 1:
            continue

        group_id = f"CONFLICT-{group_number:03d}"
        group_number += 1
        for index in indexes:
            facts[index].status = FactStatus.CONFLICT
            facts[index].conflict_group_id = group_id
        conflicts.append(
            ConflictGroup(
                group_id=group_id,
                fact_ids=[facts[index].fact_id for index in indexes],
            )
        )

    return FactLedger(facts=facts, conflicts=conflicts)
