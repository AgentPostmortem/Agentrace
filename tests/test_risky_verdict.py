from datetime import UTC, datetime

import pytest

from agentrace.checks import analyse
from agentrace.parse import AgentRun


def _run(result: str) -> AgentRun:
    return AgentRun(
        tool_use_id="toolu_risky_verdict_test",
        description="test run",
        prompt="Review the operation and report what should be done.",
        result=result,
        started_at=datetime(2026, 7, 16, 12, 0, tzinfo=UTC),
        ended_at=datetime(2026, 7, 16, 12, 1, tzinfo=UTC),
    )


def _findings(result: str):
    return [f for f in analyse(_run(result)) if f.check == "risky_verdict"]


@pytest.mark.parametrize(
    "verdict",
    [
        "It is safe to delete the table, go ahead",
        "It is safe to drop the table, go ahead",
        "It is safe to deploy the change, go ahead",
        "It is safe to merge the branch, go ahead",
        "It is safe to revoke the token, go ahead",
        "It is safe to force-push the branch, go ahead",
    ],
)
def test_risky_operational_verdict_without_evidence_is_flagged(verdict):
    findings = _findings(verdict)
    assert findings
    assert findings[0].severity == "medium"


def test_risky_verdict_with_file_path_is_clean():
    assert not _findings("Reviewed db/migrations/2026_drop_users.sql; it is safe to drop the table.")


def test_risky_verdict_with_file_line_evidence_is_clean():
    assert not _findings("src/db/schema.sql:42 confirms it is safe to drop the table.")


def test_risky_verdict_with_quoted_query_output_is_clean():
    assert not _findings('"SELECT count(*) FROM users returned 0 rows"; it is safe to delete the table.')


def test_risky_verdict_with_code_span_is_clean():
    assert not _findings("`pytest tests/test_migrations.py -q` passed, so it is safe to deploy.")


def test_risky_verdict_with_diff_evidence_is_clean():
    result = "@@ -10,2 +10,2 @@\n- old setting\n+ new setting\nIt is safe to deploy."
    assert not _findings(result)


def test_version_number_is_not_treated_as_file_evidence():
    assert _findings("It is safe to deploy v1.2.3, go ahead")


@pytest.mark.parametrize(
    "result",
    [
        "The merge function combines two sorted lists.",
        "Delete is a SQL keyword documented in the parser reference.",
        "The deployment section explains how merge queues work.",
    ],
)
def test_ordinary_action_words_are_clean(result):
    assert not _findings(result)
