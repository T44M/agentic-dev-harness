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

## 現在地: MVP-01

Phase 0 の設計・バックログ作成を終え、Python 3.12 以上で動く最小 CLI を実装しています。現在の Planner はオフラインのダミーです。実 Agent 接続、Context 収集、対象 Repository の Integration は未実装です。

最初の MVP は、次の Planner ループが GitHub Actions 上で実際に成立することです。

```text
Idea Issue
  -> 対象 Repository の薄い Workflow
  -> Harness の Planner
  -> 元 Idea Issue に Plan をコメント
  -> 人間が Plan を承認
```

詳細は [docs/DESIGN.md](docs/DESIGN.md) を参照してください。

## ローカル実行

Python 3.12 以上を使用します。実行時の外部ライブラリ依存はありません。
初回セットアップ（Repository のルートで実行）:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

セットアップ後は1コマンドでダミー Plan が出ます。GitHub 認証や Policy ファイルは不要です。

```bash
agentic-dev-harness plan --repository example/demo --issue 1
```

`python -m agentic_dev_harness plan --repository example/demo --issue 1` でも実行できます。

### 入出力契約（MVP-01）

| 入力 | 契約 |
|---|---|
| `plan` | ダミー Planner を実行するサブコマンド |
| `--repository` | 必須。`OWNER/REPO` 形式。URL は不可 |
| `--issue` | 必須。1以上の整数 |
| `--policy` | 任意。既定値 `.agent/policy.yaml`。空白のみは不可 |

Policy パスは文字列として渡すだけで、存在確認・読み込み・適用は行いません。
相対パスの起点は、後続の Loader 実装時には CLI の作業ディレクトリとします。
Repository・Issue も識別子として扱い、取得や存在確認はしません。

標準出力には JSON オブジェクトを1つだけ出力します。

```json
{
  "schema_version": 1,
  "status": "dummy",
  "request": {
    "repository": "example/demo",
    "issue_number": 1,
    "policy_path": ".agent/policy.yaml"
  },
  "plan": {
    "summary": "Dummy plan for example/demo#1",
    "steps": ["Placeholder only: no context collected or implementation performed."]
  }
}
```

`status: dummy` は動作確認用であり、実装可能な Plan や人間の承認済み状態を示しません。
Plan の本仕様・検証・Markdown 変換は MVP-05 で実装します。

| 終了コード | 意味 |
|---|---|
| `0` | 成功（`--help` を含む） |
| `1` | Planner 実行または結果の JSON 化に失敗 |
| `2` | 引数の不足・不正 |

失敗時は標準エラーへ診断を出し、標準出力には Plan を出しません。

### 開発・確認

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

同じ確認と CLI の実行を GitHub Actions で PR 時および main への push 時に行います。

### 最小構成

- `src/agentic_dev_harness/cli.py`: 引数検証・JSON 出力
- `src/agentic_dev_harness/planner.py`: Request / Result と `Planner` Protocol、DummyPlanner
- `tests/`: CLI の実プロセス実行、入力検証、Planner 差し替え・失敗のテスト
- `.github/workflows/ci.yml`: Harness 自身の Test / Lint / CLI 確認

Planner は `plan(request) -> PlannerResult` の境界で差し替えます。
特定 Agent SDK やプラグイン機構は導入していません。

## MVP の原則

- GitHub Issue を唯一の Idea 入口とする
- Repository 全体を無制限に読み込まない
- Planner が確認した Context と選定理由を Plan に残す
- Plan 承認前は Development Issue や実装を開始しない
- GitHub Actions を実行基盤とする
- 独自 Web UI、SaaS 化、複雑な Multi-Agent Framework は作らない

## Phase 0 Backlog

MVP に必要な作業は7件です。Issue本文、依存関係、完了条件は [docs/DESIGN.md](docs/DESIGN.md#phase-0-backlog) に整理しています。

1. [MVP-01: Harness CLIの最小骨格と実行契約を定義する](https://github.com/T44M/agentic-dev-harness/issues/1)
2. [MVP-02: `.agent/policy.yaml`の最小仕様とLoaderを作る](https://github.com/T44M/agentic-dev-harness/issues/2)
3. [MVP-03: 対象Repository用の薄いWorkflow契約を作る](https://github.com/T44M/agentic-dev-harness/issues/3)
4. [MVP-04: 固定Contextと限定探索のCollectorを実装する](https://github.com/T44M/agentic-dev-harness/issues/4)
5. [MVP-05: Planner実行と構造化Plan形式を実装する](https://github.com/T44M/agentic-dev-harness/issues/5)
6. [MVP-06: Planコメント投稿とHuman Gate 1を実装する](https://github.com/T44M/agentic-dev-harness/issues/6)
7. [MVP-07: `home-dns-observability`でPlannerループをE2E検証する](https://github.com/T44M/agentic-dev-harness/issues/7)

推奨する最初の Issue は [MVP-01](https://github.com/T44M/agentic-dev-harness/issues/1) です。
