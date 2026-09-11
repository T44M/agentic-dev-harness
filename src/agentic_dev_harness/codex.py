"""One fixed-input Codex connectivity check, using local ChatGPT credentials."""

import os
import signal
import subprocess
import tempfile
from pathlib import Path

from agentic_dev_harness.planner import Plan, PlannerRequest, PlannerResult

RESPONSE = "HARNESS_CODEX_OK"
PROMPT = f"Reply with exactly {RESPONSE}. Do not use tools or read any files."


class CodexSmokeError(RuntimeError):
    """A sanitized error suitable for CLI output."""


class CodexSmokePlanner:
    def __init__(self, *, timeout: int = 60):
        if not 1 <= timeout <= 300:
            raise ValueError("timeout must be between 1 and 300 seconds")
        self.timeout = timeout

    def _run(self, args: list[str], *, cwd: str, timeout: int, prompt: str = "") -> str:
        # Never forward API-key overrides or expose raw Codex logs/credentials.
        env = os.environ.copy()
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"):
            env.pop(key, None)
        try:
            with subprocess.Popen(
                [
                    "codex",
                    "-c",
                    'forced_login_method="chatgpt"',
                    "-c",
                    'model_provider="openai"',
                    *args,
                ],
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                start_new_session=True,
            ) as process:
                try:
                    stdout, stderr = process.communicate(prompt, timeout=timeout)
                except subprocess.TimeoutExpired:
                    # WSL/Linux: stop the CLI and its children, then reap it.
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    raise CodexSmokeError("Codex timed out; connection check stopped.") from None
                if process.returncode != 0:
                    raise CodexSmokeError(
                        "Codex failed; check `codex login status` and ChatGPT login, "
                        "network, usage limits, and CLI configuration."
                    )
                return stdout + "\n" + stderr
        except FileNotFoundError:
            raise CodexSmokeError("Codex CLI not found; install it inside WSL.") from None
        except OSError:
            raise CodexSmokeError("Could not run Codex CLI inside WSL.") from None

    def plan(self, request: PlannerRequest) -> PlannerResult:
        # Identifiers are deliberately not sent: no Issue or Context was fetched.
        with tempfile.TemporaryDirectory(prefix="harness-codex-") as workdir:
            status = self._run(["login", "status"], cwd=workdir, timeout=10)
            if status.strip() != "Logged in using ChatGPT":
                raise CodexSmokeError(
                    "ChatGPT login was not confirmed; run `codex login` in WSL. "
                    "API-key authentication is not supported."
                )
            response_path = Path(workdir) / "response.txt"
            self._run(
                [
                    "-a",
                    "never",
                    "exec",
                    "--sandbox",
                    "read-only",
                    "--ephemeral",
                    "--skip-git-repo-check",
                    "--output-last-message",
                    str(response_path),
                    "-",
                ],
                cwd=workdir,
                timeout=self.timeout,
                prompt=PROMPT,
            )
            try:
                response = response_path.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeError):
                raise CodexSmokeError("Codex returned no readable final response.") from None
            if response != RESPONSE:
                raise CodexSmokeError("Codex returned an unexpected final response.")
        return PlannerResult(
            schema_version=1,
            status="connection_verified",
            request=request,
            plan=Plan(
                summary="Codex ChatGPT connection verified; no Plan generated.",
                steps=(RESPONSE, "Fixed input only; Issue, Policy and Context not loaded."),
            ),
        )
