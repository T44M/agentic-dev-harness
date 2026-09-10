"""Exercise the installed CLI against a local executable, without LLM/network access."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentic_dev_harness.cli import main

ARGS = ["plan", "--repository", "example/demo", "--issue", "5", "--codex-smoke-test"]


@pytest.fixture
def fake_codex(tmp_path, monkeypatch):
    executable = tmp_path / "codex"
    executable.write_text(
        f"#!{sys.executable}\n"
        + """
import json
import os
import pathlib
import subprocess
import sys
import time

args = sys.argv[1:]
mode = os.environ.get("FAKE_MODE", "success")
with open(os.environ["CALL_LOG"], "a") as log:
    log.write(json.dumps({"args": args, "cwd": os.getcwd()}) + "\\n")
assert not any(k in os.environ for k in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"))
assert 'forced_login_method="chatgpt"' in args
assert 'model_provider="openai"' in args
if "login" in args:
    if mode == "logged_out":
        print("secret credential detail", file=sys.stderr)
        sys.exit(1)
    print("Logged in using API key: secret" if mode == "api" else
          "unknown auth format" if mode == "unknown" else "Logged in using ChatGPT",
          file=sys.stderr)
    sys.exit(0)
assert sys.stdin.read() == ("Reply with exactly HARNESS_CODEX_OK. "
                            "Do not use tools or read any files.")
assert "example/demo" not in str(args)
assert list(pathlib.Path.cwd().iterdir()) == []
assert args[args.index("--sandbox") + 1] == "read-only"
assert args[args.index("-a") + 1] == "never"
if mode == "timeout":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pathlib.Path(os.environ["CHILD_PID"]).write_text(str(child.pid))
    time.sleep(60)
if mode == "expired":
    print("expired secret token", file=sys.stderr)
    sys.exit(1)
if mode != "missing":
    result = "wrong" if mode == "wrong" else "" if mode == "empty" else "HARNESS_CODEX_OK\\n"
    pathlib.Path(args[args.index("--output-last-message") + 1]).write_text(result)
print("raw logs containing secret", file=sys.stderr)
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("CALL_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.setenv("CHILD_PID", str(tmp_path / "child.pid"))
    for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"):
        monkeypatch.setenv(key, "must-not-be-forwarded")
    return tmp_path


def run_cli():
    return subprocess.run(
        [sys.executable, "-m", "agentic_dev_harness", *ARGS, "--timeout", "1"],
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_connection_success_uses_one_fixed_inference(fake_codex):
    result = run_cli()
    assert result.returncode == 0
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["status"] == "connection_verified"
    assert "no Plan generated" in output["plan"]["summary"]
    calls = [json.loads(line) for line in (fake_codex / "calls.jsonl").read_text().splitlines()]
    assert len(calls) == 2
    assert "login" in calls[0]["args"] and "exec" in calls[1]["args"]
    assert not os.path.exists(calls[1]["cwd"])


@pytest.mark.parametrize(
    "mode,count",
    [
        ("logged_out", 1),
        ("api", 1),
        ("unknown", 1),
        ("expired", 2),
        ("missing", 2),
        ("empty", 2),
        ("wrong", 2),
        ("timeout", 2),
    ],
)
def test_failure_never_emits_success_or_secrets(fake_codex, monkeypatch, mode, count):
    monkeypatch.setenv("FAKE_MODE", mode)
    result = run_cli()
    assert result.returncode == 1
    assert result.stdout == ""
    assert "secret" not in result.stderr
    assert "Planner failed:" in result.stderr
    calls = (fake_codex / "calls.jsonl").read_text().splitlines()
    assert len(calls) == count
    if mode == "timeout":
        assert "timed out" in result.stderr
        pid = (fake_codex / "child.pid").read_text()
        stat = Path(f"/proc/{pid}/stat")
        # A killed child may briefly remain a zombie until its parent is reaped.
        assert not stat.exists() or stat.read_text().split()[2] == "Z"


def test_missing_codex(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert main(ARGS) == 1
    out = capsys.readouterr()
    assert out.out == ""
    assert "not found" in out.err


@pytest.mark.parametrize("value", ["0", "-1", "301", "nan", "inf", "1.5"])
def test_timeout_validation(value, capsys):
    with pytest.raises(SystemExit) as exc:
        main(ARGS + ["--timeout", value])
    assert exc.value.code == 2
    assert capsys.readouterr().out == ""
