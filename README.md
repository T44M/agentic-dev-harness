# Agentic Development Harness

GitHub Issue と Repository を入力として、Codex CLI を実行エンジンに使いながら Software Development Lifecycle を段階的に進める薄い Development Harness です。

このプロジェクトは Coding Agent 自体を作りません。Codex など既存の Coding Agent に Role / Context / Policy / Task を与え、SDLC 上の Stage、Human Approval、GitHub 上の状態、実行回数を Harness が制御します。

## 中心思想

目標は AI Agent Platform や汎用 Workflow Engine を作ることではありません。

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

Harness は Software Development に限定し、SDLC 上の意味を持つ固定 Stage を扱います。

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

Issue に応じて途中 Stage から開始できます。具体的な Bug であれば Implementation から、大きな Idea であれば Specification から開始する想定です。

## やらないこと

現時点では以下を作りません。

- 汎用 Workflow Builder / Canvas
- 任意 Node 接続
- 汎用 Trigger / IF / Webhook Engine
- 任意 SaaS Connector 群
- 独自 Coding Agent / 独自 LLM
- 複雑な Multi-Agent Platform
- Observability データ収集基盤
- Reporting Engine

n8n、Dify、LangGraph、OpenHands、Copilot Coding Agent 等は参考実装・競合調査対象であり、Harness の必須依存にはしません。

## Harness の責務

コア責務は以下に限定します。

- GitHub Adapter
- Repository Context
- Codex Runner
- Stage Controller
- Approval
- Policy / Usage Limits

GitHub を Development Process の SoT とします。Harness 専用 DB は必要性が確認されるまで導入しません。

## Codex 利用方針

個人 PoC / dogfooding 段階では Codex CLI + ChatGPT ログインを基本とします。OpenAI API Key による従量課金は当面導入しません。

将来的には 1 run あたりの呼び出し回数、retry、review / fix loop、timeout、Context 投入量などを制限できる設計にしますが、MVP では高度な Usage Management より成果物を確実に生成できることを優先します。

Codex 認証と GitHub 操作用認証は別に扱います。

## 現在地

共通基盤として以下まで実装・確認済みです。

- Python 3.12+ の最小 CLI
- `plan --repository --issue`
- Planner Protocol と DummyPlanner
- pytest / Ruff / GitHub Actions CI
- Codex CLI の固定入力 smoke test
- ChatGPT ログイン強制
- timeout / process stop / sanitized error
- WSL から本物の Codex CLI を実行し `HARNESS_CODEX_OK` を確認

PR #10 で WSL 実接続まで成功しています。Context 収集、実 Issue 取得、Business Requirements / Technical Specification 生成、GitHub 投稿は未実装です。

既存 CLI と Codex 接続コードは捨てず、後続 Stage の共通基盤として再利用します。

## Specification-first MVP

最初の MVP は完全自律開発ではなく、Specification Stage を成立させることです。

```text
GitHub Issue Idea
      ↓
GitHub Adapter
      ↓
Repository Context Understanding
      ↓
Business Requirements
      ↓
Technical Specification
      ↓
Human Approval
```

MVP の最重要ゴールは、GitHub Issue に Idea を書けば、Repository の実態を踏まえた Business Requirements と Technical Specification が生成され、人間がレビューできる状態になることです。

最初の dogfooding 対象は `T44M/home-dns-observability` です。

### MVP のクリティカルパス

1. [#11 GitHub Issue Adapter](https://github.com/T44M/agentic-dev-harness/issues/11)
2. [#4 Repository Context / Context Manifest](https://github.com/T44M/agentic-dev-harness/issues/4)
3. [#5 Business Requirements / Technical Specification generation](https://github.com/T44M/agentic-dev-harness/issues/5)
4. [#6 Specification posting / Human Approval Gate](https://github.com/T44M/agentic-dev-harness/issues/6)
5. [#7 home-dns-observability E2E](https://github.com/T44M/agentic-dev-harness/issues/7)

MVP は WSL からの明示的な手動起動で成立させます。GitHub Actions から Codex を起動する Integration は Specification Stage が安定してから追加します。

### MVP 後へ Defer

- [#2 `.agent/policy.yaml` Loader](https://github.com/T44M/agentic-dev-harness/issues/2): Repository 固有設定が必要になってから導入
- [#3 対象 Repository Workflow](https://github.com/T44M/agentic-dev-harness/issues/3): Actions Integration 段階で実装
- [#9 Actions / Runner / ChatGPT login 維持](https://github.com/T44M/agentic-dev-harness/issues/9): #7 完了後に再開

## Repository Context の原則

Repository 全体を無制限に Codex へ投入しません。

初期 MVP では Harness 内の安全な既定値で、README、AGENTS、主要 docs / manifest などの固定 Context と、Issue 内容に応じた限定探索を行います。何を読んだか、なぜ選んだか、不足情報、探索上限到達を Context Manifest に残します。

`.agent/policy.yaml` は将来の Repository 固有上書きとして追加できる設計にしますが、MVP の必須前提にはしません。

## Home DNS Observability との責務境界

`home-dns-observability` は Observability / Reporting 側を担当します。

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

Harness は GitHub Issue が作られたところから担当します。Observability データ収集や Reporting Engine 自体は Harness へ取り込みません。

## ローカル実行

Python 3.12 以上を使用します。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

現在のダミー CLI:

```bash
agentic-dev-harness plan \
  --repository example/demo \
  --issue 1
```

標準出力には JSON オブジェクトを1つだけ返します。現時点の `plan` は既存 CLI 契約を保持するため残しており、Specification-first MVP の完成を意味しません。

### Codex 接続確認

```bash
agentic-dev-harness plan \
  --repository T44M/home-dns-observability \
  --issue 13 \
  --codex-smoke-test
```

成功時は終了コード `0`、`status: connection_verified`、`HARNESS_CODEX_OK` を返します。これは固定入力の接続確認だけで、Issue / Repository Context は Codex へ渡しません。

詳細は [docs/CODEX_SMOKE_TEST.md](docs/CODEX_SMOKE_TEST.md) を参照してください。

## 現在のコード構成

```text
src/agentic_dev_harness/
├── cli.py       CLI / input validation / JSON output
├── planner.py   現行 Request / Result / Planner Protocol / DummyPlanner
└── codex.py     Codex smoke-test execution

tests/
├── test_cli.py
└── test_codex.py
```

現行コードは薄く、汎用 Workflow Engine 的な抽象化は入っていません。Specification 実装時に必要であれば Codex 実行部分を Stage 非依存の小さな Runner へ抽出しますが、Plugin Framework や任意 Node 機構は導入しません。

## 開発・確認

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

## 次の開発順

次は #11 の GitHub Issue Adapter です。その後 #4 → #5 → #6 → #7 の順に Specification Stage を完成させます。

Planning / Implementation / Validation は Specification-first MVP が成立してから、必要な最小単位で追加します。

詳細設計は [docs/DESIGN.md](docs/DESIGN.md) を参照してください。
