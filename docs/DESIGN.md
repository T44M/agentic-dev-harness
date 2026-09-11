# Agentic Development Harness — Design

## 1. Purpose

`agentic-dev-harness` is a thin control layer between GitHub and existing Coding Agents such as Codex.

It does not implement a Coding Agent. It coordinates Software Development Lifecycle stages, repository context, human approval, execution state, and usage limits while delegating reasoning and code generation to Codex CLI.

The project targets Software Development only. It is intentionally not a general-purpose Workflow / Agent Orchestration platform.

## 2. Core flow

```text
GitHub Issue / Repository
        ↓
agentic-dev-harness
        ↓
Codex CLI
        ↓
Spec / Plan / Code / Test / PR
        ↓
GitHub
```

GitHub is the Development Process source of truth. A Harness-specific database is not introduced until GitHub state proves insufficient.

## 3. Explicit non-goals

The Harness must not drift into the following without a demonstrated SDLC requirement:

- generic Workflow Builder / Canvas
- arbitrary Node graphs
- generic Trigger / IF / Webhook engine
- arbitrary SaaS connector framework
- custom Coding Agent
- custom LLM
- generic Multi-Agent platform
- Observability data collection
- Reporting engine

Products such as n8n, Dify, LangGraph, OpenHands, and Copilot Coding Agent may be used as reference implementations or competitors, but are not mandatory runtime dependencies.

## 4. SDLC Stage model

The Harness understands fixed SDLC stages.

```text
SPECIFICATION
    ↓
PLANNING
    ↓
IMPLEMENTATION
    ↓
VALIDATION
    ↓
DONE
```

These are semantic development stages, not replaceable workflow nodes.

An Issue may start from a later stage when appropriate.

Examples:

```text
Feature / Idea
SPECIFICATION → PLANNING → IMPLEMENTATION → VALIDATION

Concrete Bug
IMPLEMENTATION → VALIDATION
```

The future Stage Controller therefore only needs a small state machine that selects a valid start stage and controls allowed transitions.

## 5. Stage definitions

### 5.1 Specification

Input: GitHub Issue containing an Idea, requirement, or problem statement.

```text
Idea
 ↓
Repository / Context Understanding
 ↓
Business Requirements
 ↓
Technical Specification
 ↓
Human Approval
```

This stage normally does not modify product code.

Minimum Business Requirements:

- Idea / Problem understanding
- desired Outcome
- Scope / Out of Scope
- Acceptance Criteria
- assumptions and questions

Minimum Technical Specification:

- relationship to the current Repository
- candidate components / responsibility boundaries
- technical approach
- test / validation approach
- risks and constraints
- unresolved items
- Context Manifest reference

### 5.2 Planning

Input: approved Specification.

```text
Specification
 ↓
Implementation Plan
 ↓
Issue decomposition
 ↓
Dependency / execution order
 ↓
Human Approval
```

Planning converts the approved Specification into implementation-sized GitHub Issues.

Planning is not part of the first MVP.

### 5.3 Implementation

Input: implementation Issue.

```text
Issue
 ↓
Codex Implementation
 ↓
Test
 ↓
Review
 ↓
Fix loop
 ↓
PR
```

Harness controls Role, Context, Policy, execution order, retry, and state. Developer / Reviewer intelligence remains in Codex or another Coding Agent.

Implementation is not part of the first MVP.

### 5.4 Validation

Input: implementation result.

```text
Implementation Result
 ↓
Integration / E2E
 ↓
Requirements Validation
 ↓
Documentation Validation
 ↓
Release Readiness
 ↓
Human Approval
```

Validation may return to Implementation when requirements are not satisfied.

Validation is not part of the first MVP.

## 6. Core components

```text
agentic-dev-harness
│
├── GitHub Adapter
├── Repository Context
├── Codex Runner
├── Stage Controller
├── Approval
└── Policy / Usage Limits
```

### 6.1 GitHub Adapter

Responsibilities are limited to the GitHub operations needed by the SDLC:

- fetch Issue
- create/update Issue and comments
- create implementation Issues
- create PR
- read/write minimal state

Do not build a generic connector layer.

For the local MVP, GitHub authentication is separate from Codex authentication. The first implementation may use the existing `gh` CLI login available in WSL.

### 6.2 Repository Context

Repository Context constructs bounded evidence for Codex.

Initial fixed entry points may include:

- `README.md`
- `AGENTS.md` when present
- key documents under `docs/`
- dependency / runtime manifests

The Issue text is then used to perform limited exploration of related source, tests, and configuration.

Rules:

- never pass the whole Repository by default
- record each selected file/range and why it was selected
- distinguish missing information from exploration-limit exhaustion
- exclude secrets, generated outputs, very large files, and repository-external credentials

The result is a Context Manifest containing:

- files / ranges inspected
- selection reasons
- missing information
- assumptions
- exploration-limit state

The first MVP uses safe built-in defaults. `.agent/policy.yaml` is an optional post-MVP override rather than an MVP prerequisite.

### 6.3 Codex Runner

Codex CLI is the initial execution engine.

Authentication policy:

- use ChatGPT login for personal PoC / dogfooding
- do not require OpenAI API Key in the MVP
- keep GitHub and Codex authentication separate
- do not expose raw credentials or raw sensitive logs

PR #10 already proved real WSL execution with ChatGPT login and the fixed response `HARNESS_CODEX_OK`.

The current `CodexSmokePlanner` implementation is retained. When Specification generation needs it, only the process-execution portion should be extracted into a small Stage-independent runner. This extraction must not become an Agent SDK or Plugin Framework.

### 6.4 Stage Controller

The Stage Controller eventually owns only the small SDLC transition model.

Initial conceptual states:

```text
SPECIFICATION
PLANNING
IMPLEMENTATION
VALIDATION
DONE
BLOCKED
```

Not every Issue starts at `SPECIFICATION`.

The first MVP does not require the complete controller. It only needs enough state to hold Specification output and wait for human approval.

### 6.5 Approval

Important boundaries require explicit human approval.

Initial targets:

- Specification approval
- Planning approval
- optional PR / Release approval

Specification approval must be tied to a particular version. If the Specification changes, approval must be requested again.

### 6.6 Policy / Usage Limits

Long-term controls may include:

- agent calls per run
- retry count
- review / fix loop count
- timeout
- Context limits
- protection against unnecessary Codex execution

The MVP implements only limits required for safety and predictable execution. It does not build advanced quota management.

## 7. Repository boundary

### Harness Repository

`T44M/agentic-dev-harness` contains the control logic.

### Target Repository

The target repository does not contain the Harness implementation.

A thin integration may later be added, for example:

```text
.agent/policy.yaml
.github/workflows/agent.yml
```

Neither is mandatory for the first Specification MVP.

## 8. Home DNS Observability boundary

The first dogfooding target is `T44M/home-dns-observability`.

Home DNS remains responsible for Observability and Reporting up to Issue creation.

```text
Prometheus / Loki
       ↓
DNS Report
       ↓
Finding
       ↓
GitHub Issue
────────────── Harness Boundary
       ↓
Specification / Planning
       ↓
Implementation
       ↓
Validation
       ↓
PR
```

The Harness does not ingest Prometheus / Loki directly and does not own DNS Reporting.

This preserves the future improvement loop without merging unrelated responsibilities:

```text
Observability
 ↓
Report
 ↓
Finding
 ↓
Issue
 ↓
Harness
 ↓
Improvement
 ↓
Deploy
 ↓
Observability
```

## 9. Existing implementation to retain

The following are common foundation and remain valid:

- Python 3.12+ package structure
- CLI entrypoint
- `--repository`
- `--issue`
- current JSON output contract as an early compatibility surface
- Planner Protocol / DummyPlanner as existing test seams
- pytest / Ruff CI
- Codex CLI subprocess execution
- ChatGPT login enforcement
- API-key override removal for the smoke path
- timeout and child-process termination
- sanitized error output
- real WSL Codex connectivity verification

The codebase is currently small and does not contain a generic Workflow Engine. No rewrite is required.

Semantic names such as `Planner` may be refactored only when the Specification implementation requires it. Backward compatibility is preferable to speculative cleanup.

## 10. Specification-first MVP

### 10.1 Goal

The MVP is complete when a real GitHub Idea Issue can produce a repository-grounded Business Requirements document and Technical Specification that a human can review and approve.

```text
GitHub Issue Idea
      ↓
Issue retrieval
      ↓
Repository Context
      ↓
Business Requirements
      ↓
Technical Specification
      ↓
Issue comment
      ↓
Human Approval
```

### 10.2 Execution model

The MVP may be started manually from WSL.

GitHub Actions is not an MVP completion requirement. This intentionally avoids spending the first MVP on Runner placement and ChatGPT-login lifecycle before the Specification contract is proven.

### 10.3 MVP critical path

1. #11 — GitHub Issue Adapter
2. #4 — Repository Context Collector / Context Manifest
3. #5 — Business Requirements / Technical Specification generation
4. #6 — Specification posting / Human Approval Gate
5. #7 — `home-dns-observability` E2E

### 10.4 MVP completion criteria

Using a real `home-dns-observability` Idea Issue:

1. Harness fetches the real Issue body.
2. Harness inspects bounded Repository Context.
3. Context Manifest records the evidence used.
4. Codex generates Business Requirements.
5. Codex generates Technical Specification.
6. Missing information is surfaced instead of guessed.
7. The Specification is posted to the originating Issue.
8. A human can approve a specific Specification version.
9. Harness can distinguish approved from unapproved state.
10. No product-code implementation is started automatically.

## 11. Backlog classification after design realignment

| Issue | Classification | Stage / role | Decision |
|---|---|---|---|
| #1 | Keep | Shared foundation | Completed CLI / test foundation remains valid |
| #2 | Defer | Policy | Optional repository-specific overrides after Context contract is proven |
| #3 | Defer | Integration | GitHub Actions workflow after Specification MVP |
| #4 | Modify | Specification | Context Collector becomes MVP-SPEC-02 and no longer depends on #2 |
| #5 | Modify | Specification | Replace old structured Plan goal with Business Requirements / Technical Specification; keep smoke-test work |
| #6 | Modify | Specification | Plan Gate becomes Specification Approval Gate |
| #7 | Modify | Specification | E2E becomes manual-WSL Specification Stage dogfood |
| #9 | Defer | Execution infrastructure | Actions / Runner / login lifecycle after #7 |
| #11 | New | Specification | Real GitHub Issue input Adapter |

No existing Issue needs to be discarded purely because of the new direction.

There is currently no active Planning / Implementation / Validation backlog. Those stages should be created only after Specification MVP results expose the actual interfaces they need.

## 12. Development order

The next work is intentionally narrow:

```text
#11 GitHub Issue Adapter
  ↓
#4 Repository Context
  ↓
#5 Specification generation
  ↓
#6 Human Approval
  ↓
#7 E2E dogfood
```

After #7:

1. inspect dogfooding findings
2. define the minimal Planning Stage
3. add issue decomposition and Planning approval
4. then design Implementation / Validation loops
5. separately resume #9 and #3 when Actions-based execution is useful

## 13. Guardrails against scope creep

When considering a new abstraction, ask:

1. Is it required by a concrete SDLC Stage?
2. Is it required by at least one current dogfooding case?
3. Can the requirement be solved by a small GitHub / Repository / Codex adapter instead?
4. Would the abstraction move the project toward a generic workflow platform?

If the answer to 4 is yes and the requirement is not proven, defer it.
