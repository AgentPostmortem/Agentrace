from __future__ import annotations

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentrace.cli", *args],
        capture_output=True,
        check=False,
        text=True,
    )


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


def test_empty_result_names_selected_directory(tmp_path):
    result = run_cli("--dir", str(tmp_path), "list")

    assert result.returncode == 0
    assert "No subagent runs found." in result.stdout
    assert f"Looked in {tmp_path}." in result.stdout
