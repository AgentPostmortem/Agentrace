from datetime import datetime, timezone

from agentrace.checks import analyse
from agentrace.parse import AgentRun


def _run(result: str) -> AgentRun:
    return AgentRun(
        tool_use_id="toolu_destructive_test",
        description="test run",
        prompt="Review the operation and report what should be run.",
        result=result,
        started_at=datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 7, 16, 12, 1, tzinfo=timezone.utc),
    )


def _findings(result: str):
    return [f for f in analyse(_run(result)) if f.check == "destructive_command"]


def test_destructive_command_flags_rm_rf_without_warning():
    findings = _findings("Run: rm -rf /data/cache")
    assert findings
    assert findings[0].severity == "high"


def test_destructive_command_allows_rm_rf_with_dry_run_warning():
    assert not _findings("Verify with a dry-run first, then run: rm -rf /data/cache")


def test_destructive_command_flags_drop_table_without_warning():
    assert _findings("Execute: DROP TABLE users;")


def test_destructive_command_flags_kubectl_delete_without_warning():
    assert _findings("Run kubectl delete namespace production")


def test_destructive_command_allows_command_with_backup_warning():
    assert not _findings("Take a backup before running: DROP TABLE users;")


def test_destructive_command_ignores_unrelated_safe_output():
    assert not _findings("Run pytest -q and review the failures before making changes.")
