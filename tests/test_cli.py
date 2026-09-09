from __future__ import annotations

import subprocess
import sys
from argparse import Namespace
from datetime import UTC, datetime, timedelta

import pytest

from agentrace import cli
from agentrace.parse import AgentRun


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentrace.cli", *args],
        capture_output=True,
        check=False,
        text=True,
    )


@pytest.mark.parametrize(
    "durations,expected",
    [
        ([10, 20], "15 s"),
        ([30, 10, 20], "20 s"),
        ([10], "10 s"),
        ([10, None, 20], "15 s"),
        ([None], None),
    ],
)
def test_stats_median(durations, expected, monkeypatch, capsys):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    runs = [
        AgentRun(
            tool_use_id=str(i),
            description="test",
            prompt="prompt",
            result="result",
            started_at=start,
            ended_at=start + timedelta(seconds=duration) if duration is not None else None,
        )
        for i, duration in enumerate(durations)
    ]
    monkeypatch.setattr(cli, "_load", lambda args: runs)

    assert cli.cmd_stats(Namespace(json=False)) == 0

    rows = capsys.readouterr().out.splitlines()
    median_rows = [row for row in rows if "median run" in row]
    if expected is None:
        assert median_rows == []
    else:
        assert len(median_rows) == 1
        assert " ".join(median_rows[0].split()) == f"median run {expected}"


def test_stats_excludes_clock_skewed_duration(monkeypatch, capsys):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    runs = [
        AgentRun(
            tool_use_id=str(i),
            description="test",
            prompt="prompt",
            result="result",
            started_at=start,
            ended_at=start + timedelta(seconds=duration),
        )
        for i, duration in enumerate([-5, 10, 20])
    ]
    monkeypatch.setattr(cli, "_load", lambda args: runs)
    assert cli.cmd_stats(Namespace(json=True)) == 0
    output = capsys.readouterr().out
    assert '"total_seconds": 30.0' in output
    assert "median run 15 s" in " ".join(output.split())
    assert runs[0].duration_s is None


def test_file_and_dir_are_mutually_exclusive(tmp_path):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("")

    result = run_cli("--dir", str(tmp_path), "--file", str(transcript), "list")

    assert result.returncode == 2
    assert "argument --file: not allowed with argument --dir" in result.stderr
    assert result.stdout == ""


def test_missing_file_is_a_clean_parser_error(tmp_path):
    missing = tmp_path / "missing.jsonl"

    result = run_cli("--file", str(missing), "list")

    assert result.returncode == 2
    assert f"not a file: {missing}" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""


def test_empty_result_names_selected_file(tmp_path):
    transcript = tmp_path / "empty.jsonl"
    transcript.write_text("")

    result = run_cli("--file", str(transcript), "list")

    assert result.returncode == 0
    assert "No subagent runs found." in result.stdout
    assert f"Looked in {transcript}." in result.stdout
    
def test_show_empty_id_errors(tmp_path):
    transcript = tmp_path / "empty.jsonl"
    transcript.write_text("")
    result = run_cli("--file", str(transcript), "show", "")

    assert result.returncode == 1
    assert "Please provide a run ID" in result.stderr


def test_empty_result_names_selected_directory(tmp_path):
    result = run_cli("--dir", str(tmp_path), "list")

    assert result.returncode == 0
    assert "No subagent runs found." in result.stdout
    assert f"Looked in {tmp_path}." in result.stdout

def test_dir_given_file_hints_to_use_file(tmp_path):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("")
    result = run_cli("--dir", str(transcript), "list")
    assert "--file" in result.stdout


def test_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
