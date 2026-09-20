"""Student State & Taught — pure domain rules, NO I/O (doc 03 §3.1).

doc 13 §13.6: state dimensions are self-report (check-in).
doc 08 §8.8: taught cascades parent→child; parent may be indeterminate.
"""
from __future__ import annotations

from app.modules.student.models import CHECKIN_DIMENSIONS


def validate_checkin_payload(dims: dict) -> list[str]:
    """Return Persian error list (empty when valid). Scale 1..5 (doc 13 §13.6)."""
    errors: list[str] = []
    for d in CHECKIN_DIMENSIONS:
        v = dims.get(d)
        if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 5):
            errors.append(f"{d} باید عددی بین ۱ تا ۵ باشد.")
    return errors


def state_summary(today, last, data_days: int) -> dict:
    """Shape of GET /students/me/state — never mixes today/last."""
    return {"today": today, "last": last, "data_days": data_days}


def apply_taught(
    existing: dict[str, bool],
    changes: list[tuple[str, bool]],
    children_map: dict[str, list[str]] | None = None,
) -> dict[str, bool]:
    """doc 08 §8.8 — taught parent→child cascade.

    - setting a topic taught=True marks all (transitive) descendants taught=True
    - setting taught=False never un-teaches descendants
    - children_map: topic_id -> [child topic_ids] (phase 2 supplies the real tree;
      phase 1 runs with an empty map, so behavior is a plain upsert)
    """
    children_map = children_map or {}
    result = dict(existing)

    def cascade(tid: str, value: bool) -> None:
        result[tid] = value
        if value:
            for child in children_map.get(tid, []):
                if not result.get(child, False):
                    cascade(child, True)

    for tid, value in changes:
        cascade(tid, value)
    return result


def parent_state(child_states: list[bool]) -> str:
    """doc 08 §8.8 — parent may be indeterminate: 'all' | 'none' | 'partial'."""
    if not child_states:
        return "none"
    if all(child_states):
        return "all"
    if not any(child_states):
        return "none"
    return "partial"
