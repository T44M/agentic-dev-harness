# WSL Codex connectivity smoke test

This check verifies only that the Harness can invoke Codex CLI in WSL using ChatGPT login and receive a fixed response.

It does **not** fetch the Issue, collect Repository Context, generate a Business Requirements / Technical Specification, or post to GitHub.

## Command

Use Python 3.12+ and Codex CLI inside WSL.

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'
codex --version
codex login status

agentic-dev-harness plan \
  --repository T44M/home-dns-observability \
  --issue 13 \
  --codex-smoke-test \
  --timeout 60

echo $?
```

The repository and Issue number are identifiers in the current smoke-test output. The smoke test deliberately does not fetch or send their contents to Codex.

## Success criteria

- exit code `0`
- JSON `status` is `connection_verified`
- output contains `HARNESS_CODEX_OK`

## Authentication and execution rules

- Codex must report ChatGPT login.
- API-key overrides are removed from the child environment for this path.
- GitHub authentication is separate from Codex authentication.
- The test runs from an empty temporary directory.
- Codex uses read-only sandboxing, no approval prompts, and an ephemeral session.
- Login check timeout is 10 seconds.
- Inference timeout defaults to 60 seconds and may be set from 1 to 300 seconds.
- Timeout kills the WSL/Linux process group and does not automatically retry.
- Raw Codex logs are not surfaced as the CLI error message.

Failures such as missing CLI, missing/expired ChatGPT login, unexpected authentication mode, execution failure, unreadable response, unexpected response, and timeout return a failure rather than being treated as a successful connection.

## Verification status

PR #10 (`feat: add Codex ChatGPT connectivity smoke test`) was merged after successful verification on the user's WSL environment on 2026-09-11 JST.

Verified result:

```text
status: connection_verified
HARNESS_CODEX_OK
```

GitHub Actions also passed for the offline test suite. Real Codex connectivity remains a manual check; normal CI does not use the user's ChatGPT credentials or perform live LLM calls.

## Relationship to the current MVP

The smoke test is retained as a common Codex execution foundation.

The Specification-first MVP continues with:

```text
#11 GitHub Issue Adapter
  ↓
#4 Repository Context
  ↓
#5 Business Requirements / Technical Specification generation
  ↓
#6 Human Approval
  ↓
#7 E2E dogfood
```

When #5 needs real generation, the existing process-execution logic may be extracted into a small Stage-independent Codex Runner. The project must not turn this into a generic Agent SDK or Workflow Engine.
