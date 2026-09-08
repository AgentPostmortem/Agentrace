"""Timestamp ordering and duration regressions for parsed transcripts."""

import json
from datetime import timedelta

import pytest

from agentrace.parse import parse_session


@pytest.mark.parametrize("earlier_timestamp", ["2026-09-08T10:00:00", "2026-09-08T11:00:00+01:00"])
def test_mixed_timezones_sort_by_instant(tmp_path, earlier_timestamp):
    transcript = tmp_path / "mixed.jsonl"
    records = [
        {
            "timestamp": timestamp,
            "message": {"content": [{"type": "tool_use", "name": "Agent", "id": run_id}]},
        }
        for run_id, timestamp in [
            ("later", "2026-09-08T10:01:00Z"),
            ("earlier", earlier_timestamp),
        ]
    ]
    records.append(
        {
            "timestamp": "2026-09-08T10:00:30Z",
            "message": {
                "content": [{"type": "tool_result", "tool_use_id": "earlier", "content": "done"}]
            },
        }
    )
    transcript.write_text("\n".join(json.dumps(record) for record in records))

    runs = parse_session(transcript).runs

    assert [run.tool_use_id for run in runs] == ["earlier", "later"]
    assert runs[0].duration_s == 30
    assert runs[0].started_at.utcoffset() is not None
    assert runs[1].started_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize("missing_timestamp", [None, "not-a-timestamp"])
def test_missing_timestamp_sorts_before_aware_timestamp(tmp_path, missing_timestamp):
    transcript = tmp_path / "missing.jsonl"
    records = [
        {
            "timestamp": timestamp,
            "message": {"content": [{"type": "tool_use", "name": "Agent", "id": run_id}]},
        }
        for run_id, timestamp in [
            ("known", "2026-09-08T10:00:00Z"),
            ("unknown", missing_timestamp),
        ]
    ]
    transcript.write_text("\n".join(json.dumps(record) for record in records))

    runs = parse_session(transcript).runs

    assert [run.tool_use_id for run in runs] == ["unknown", "known"]
    assert runs[0].duration_s is None
