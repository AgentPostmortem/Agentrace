import pytest

from agentrace import cli


@pytest.mark.parametrize("value", ["-1", "-5"])
def test_negative_limit_rejected_before_loading(value, monkeypatch, capsys):
    def unexpected_load(args):
        pytest.fail("invalid --max must be rejected before loading transcripts")

    monkeypatch.setattr(cli, "_load", unexpected_load)
    with pytest.raises(SystemExit) as exc:
        cli.main(["show", "abc", "--max", value])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "--max" in captured.err
    assert "non-negative" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "options, expected",
    [([], 4000), (["--max", "0"], 0), (["--max", "1"], 1), (["--max", "100"], 100)],
)
def test_nonnegative_limit_and_default(options, expected, monkeypatch):
    seen = []

    def show(args):
        seen.append(args.max)
        return 0

    monkeypatch.setattr(cli, "cmd_show", show)
    assert cli.main(["show", "abc", *options]) == 0
    assert seen == [expected]
