# Agentic Development Harness

GitHub Issue を起点に、既存の Coding Agent を制御して開発を進めるための上位レイヤーです。

このプロジェクトは Coding Agent 自体を作りません。Codex や Claude Code などを Planner、Developer、Reviewer として呼び出し、GitHub 上の状態、承認ゲート、実行回数、引き継ぐ Context を管理します。

## 目指すフロー

```text
Idea Issue
  -> Planner
  -> Human Gate 1: Plan 承認
  -> Development Issue 作成（最大5件）
  -> Developer
  -> Test / Lint
  -> Reviewer
  -> 修正（最大3回）
  -> Pull Request
  -> Human Gate 2: 確認・Merge
  -> 次の Issue
```

Merge は常に人間が行います。既存アーキテクチャ内の変更とライブラリ追加は自律実行できますが、アーキテクチャ変更には人間の承認が必要です。

## Repository の分担

- `agentic-dev-harness`: Planner、Developer、Reviewer、Retry、GitHub 状態管理などの本体
- 対象 Repository: `.github/workflows/agent.yml` と `.agent/policy.yaml` だけを持つ薄い Integration

最初の dogfooding 対象は `home-dns-observability` です。

## 現在地: Phase 0

Phase 0 は設計と開発バックログの作成だけを対象とします。Harness の実行コードや `home-dns-observability` 側の Integration はまだ実装しません。

最初の MVP は、次の Planner ループが GitHub Actions 上で実際に成立することです。

```text
Idea Issue
  -> 対象 Repository の薄い Workflow
  -> Harness の Planner
  -> 元 Idea Issue に Plan をコメント
  -> 人間が Plan を承認
```

詳細は [docs/DESIGN.md](docs/DESIGN.md) を参照してください。

## Phase 0 の構成

```text
agentic-dev-harness/
├── README.md
└── docs/
    └── DESIGN.md
```

実装開始後に必要になった時点で、`src/`、`tests/`、`templates/` を追加します。空の将来用ディレクトリは先に作りません。

## MVP の原則

- GitHub Issue を唯一の Idea 入口とする
- Repository 全体を無制限に読み込まない
- Planner が確認した Context と選定理由を Plan に残す
- Plan 承認前は Development Issue や実装を開始しない
- GitHub Actions を実行基盤とする
- 独自 Web UI、SaaS 化、複雑な Multi-Agent Framework は作らない

## Phase 0 Backlog

MVP に必要な作業は7件です。Issue本文、依存関係、完了条件は [docs/DESIGN.md](docs/DESIGN.md#phase-0-backlog) に整理しています。

推奨する最初の Issue は **Harness CLI の最小骨格と実行契約を定義する** です。
