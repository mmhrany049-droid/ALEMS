"""Settings — application services.

ذخیره در app_metadata (migration 0001) به‌صورت کلید/مقدار — همان جایی که
activity.get_penalty_k از فاز ۳ می‌خواند، پس PUT /settings بلافاصله روی
درصد کنکوری و چرخه مرور اثر می‌گذارد (بدون hard-code پراکنده، doc 10 §10.4).
"""
from __future__ import annotations

import json

from fastapi.exceptions import HTTPException

from app.core.versioning import get_meta_value, set_meta_value
from app.modules.settings import domain

KEY_INTERVALS = "review_intervals"
KEY_INCLUDE_BLANK = "include_blank_in_review"
KEY_MAX_DAILY = "max_daily_review"
KEY_MIN_CLUSTER = "min_cluster"
KEY_PENALTY_K = "konkurs_penalty_k"


def get_all(db) -> dict:
    try:
        intervals = json.loads(get_meta_value(db, KEY_INTERVALS) or "null")
        if not isinstance(intervals, list) or not intervals:
            intervals = list(domain.DEFAULT_REVIEW_INTERVALS)
    except (TypeError, ValueError):
        intervals = list(domain.DEFAULT_REVIEW_INTERVALS)

    return {
        "review_intervals": [int(x) for x in intervals],
        "include_blank_in_review": (get_meta_value(db, KEY_INCLUDE_BLANK, "false") == "true"),
        "max_daily_review": int(get_meta_value(db, KEY_MAX_DAILY, str(domain.DEFAULT_MAX_DAILY_REVIEW))),
        "min_cluster": int(get_meta_value(db, KEY_MIN_CLUSTER, str(domain.DEFAULT_MIN_CLUSTER))),
        "konkurs_penalty_k": float(get_meta_value(db, KEY_PENALTY_K, str(domain.DEFAULT_PENALTY_K))),
    }


def update(db, payload) -> dict:
    data = payload.model_dump(exclude_unset=True)
    errors = domain.validate_settings(data)
    if errors:
        raise HTTPException(status_code=422, detail=errors[0])

    if "review_intervals" in data and data["review_intervals"] is not None:
        set_meta_value(db, KEY_INTERVALS, json.dumps([int(x) for x in data["review_intervals"]]))
    if "include_blank_in_review" in data and data["include_blank_in_review"] is not None:
        set_meta_value(db, KEY_INCLUDE_BLANK, "true" if data["include_blank_in_review"] else "false")
    if "max_daily_review" in data and data["max_daily_review"] is not None:
        set_meta_value(db, KEY_MAX_DAILY, str(int(data["max_daily_review"])))
    if "min_cluster" in data and data["min_cluster"] is not None:
        set_meta_value(db, KEY_MIN_CLUSTER, str(int(data["min_cluster"])))
    if "konkurs_penalty_k" in data and data["konkurs_penalty_k"] is not None:
        set_meta_value(db, KEY_PENALTY_K, str(float(data["konkurs_penalty_k"])))
    db.flush()
    return get_all(db)
