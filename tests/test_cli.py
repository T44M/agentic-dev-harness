import json
import subprocess
import sys

import pytest

from agentic_dev_harness.cli import main
from agentic_dev_harness.planner import Plan, PlannerRequest, PlannerResult

ARGS = ["plan", "--repository", "example/demo", "--issue", "42"]


@pytest.mark.parametrize(
    "entrypoint", [[sys.executable, "-m", "agentic_dev_harness"], ["agentic-dev-harness"]]
)
def test_installed_cli_returns_dummy_json(entrypoint, tmp_path):
    result = subprocess.run(entrypoint + ARGS, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["schema_version"] == 1
    assert output["status"] == "dummy"
    assert output["request"] == {
        "repository": "example/demo",
        "issue_number": 42,
        "policy_path": ".agent/policy.yaml",
    }
    assert "example/demo#42" in output["plan"]["summary"]
    assert output["plan"]["steps"]
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["unknown"],
        ["plan"],
        ["plan", "--repository", "demo", "--issue", "1"],
        ["plan", "--repository", "https://github.com/example/demo", "--issue", "1"],
        ["plan", "--repository", "example/..", "--issue", "1"],
        *[ARGS[:-1] + [value] for value in ["0", "-1", "abc", "1.5"]],
        ARGS + ["--policy", "   "],
    ],
)
def test_invalid_input_fails_without_json(args, capsys):
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "error:" in output.err


def test_planner_can_be_replaced_and_receives_policy(capsys):
    class FakePlanner:
        def plan(self, request):
            assert request == PlannerRequest("example/demo", 42, "custom policy.yaml")
            return PlannerResult(1, "test", request, Plan("replacement", ()))

    assert main(ARGS + ["--policy", "custom policy.yaml"], planner=FakePlanner()) == 0
    assert json.loads(capsys.readouterr().out)["plan"]["summary"] == "replacement"


def test_planner_failure_is_stderr_only(capsys):
    class FailingPlanner:
        def plan(self, request):
            raise RuntimeError("test failure")

    assert main(ARGS, planner=FailingPlanner()) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "test failure" in output.err


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "plan" in capsys.readouterr().out
