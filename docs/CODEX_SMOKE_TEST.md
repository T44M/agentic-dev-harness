# WSLでのCodex接続確認（#5の一部）

固定入力への応答を確認するだけの手順です。Issue本文・Policy・Contextの取得、
構造化Plan生成、GitHub投稿は実装していません。#5全体の完了にはしません。

## WSLで実行

WSL内のPython 3.12以上とCodex CLIを使用します。Windows側のCLIではなく、
`command -v codex`でWSL内の実行ファイルを確認してください。

```bash
git fetch origin
git switch --track origin/feat/issue-5-codex-smoke
source .venv/bin/activate
python -m pip install -e '.[dev]'
codex --version
codex login status
```

未ログインの場合は`codex login`でChatGPTログインしてください。既にChatGPTで
ログイン済みなら再ログイン不要です。APIキー認証は本チェックでは受け付けません。
認証ファイルやトークンをPR・Issueに貼り付けないでください。

```bash
agentic-dev-harness plan \
  --repository T44M/home-dns-observability \
  --issue 13 \
  --codex-smoke-test \
  --timeout 60
echo $?
```

成功条件は終了コード`0`、JSONの`status`が`connection_verified`、
`plan.steps`に`HARNESS_CODEX_OK`があることです。`plan`という既存の出力フィールドを
再利用していますが、これはPlan生成成功を意味しません。
Repository・Issue番号は出力の識別子のみで、存在確認もCodexへの送信もしません。

確認後、PRにCodexバージョン、終了コード、上記status、実施日時を記録します。
このPRをマージする操作は本手順に含めません。

## 実行と失敗の扱い

- `Planner.plan(request)`から、ログイン状態確認を1回、`codex exec`を1回呼びます。
- ChatGPT認証とOpenAI providerを指定し、APIキー環境変数を子プロセスから除きます。
- `codex login status`の既知のChatGPT表示だけを受け付け、不明な形式は停止します。
  CLI更新で表示が変わった場合も、認証モードを推測して続行しません。
- 空の一時ディレクトリから、stdinで固定入力を渡します。`read-only` sandbox、
  承認要求なし（`never`）、`--ephemeral`を指定し、最終応答ファイルを厳密照合します。
- ログイン確認は10秒、推論は既定60秒（`--timeout`で1〜300秒）で打ち切ります。
  WSL/Linuxのプロセスグループを終了し、自動再試行しません。
- 未ログイン、認証切れ、実行エラー、空・不正な応答、タイムアウトは終了コード`1`。
  引数不正は`2`。失敗時はstdoutを空にし、stderrに診断だけを返します。
- 生のCodexログをそのまま表示しません。失敗時はWSL内で`codex login status`、
  ネットワーク・利用上限・CLI設定を確認してください。

現在の設定・モデルは利用者のCodex設定に依存します。既存のユーザー設定やMCP等を
全面隔離する実装ではありません。固定入力でツールを使わないよう指示していますが、
Collectorの探索上限を強制する実行境界の完成・検証は#5後半の対象です。
CLIが`--ephemeral`等に対応していない場合はエラー終了するため、CLIの更新を確認します。

## 検証状況

- WorkのLinux/Python 3.12環境：偽Codex実行ファイルを用いたプロセステスト。
  正常応答、認証モード拒否、未ログイン・認証切れ、応答欠落・不正、
  タイムアウトと子プロセス停止、機密を含むログの非表示を確認します。
- WSLでの本物のCodex＋ChatGPT接続：**未実施**。Workから利用者のWSLへは接続できず、
  この環境にCodex CLIと利用者のChatGPT資格情報もありません。上記手順での確認が必要です。
- 通常CIはネットワークやLLMを使わないテストのみ。実接続テストは手動です。

実装の参照元：
[Codex CLI reference](https://developers.openai.com/codex/cli/reference/)、
[Configuration reference](https://developers.openai.com/codex/config-reference/)。
