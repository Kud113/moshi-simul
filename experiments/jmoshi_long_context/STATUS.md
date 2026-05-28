# STATUS — J-Moshi 長文脈評価ハーネス 進捗ダイジェスト

> claude.ai のチャットから「今どこまで進んだ？最近何を変えた？」に答えるための単一の真実源。
> 上半分（AC 進捗・次の一手）は手動メンテ、下半分の `AUTO:BEGIN/END` ブロックは
> `tools/gen_digest.py`（またはサブエージェント `progress-digest`）が git から自動生成します。

## 受け入れ条件（spec §15: AC-1 .. AC-7）

凡例: ☐ 未着手 / ◐ 進行中 / ☑ 完了

- ◐ **AC-1 リポジトリ整備**: `experiments/jmoshi_long_context/` と `spec.md` は存在。
  ディレクトリ雛形あり。`pytest` は本 Epic で追加した `tests/test_docs.py` 等を発見可能。
  ただし `run_long_dialogue.py` / `kv_policy.py` / `configs/*.yaml` 等の必須スクリプトは未作成。
- ☐ **AC-2 入力生成**: Ollama / HF プロバイダ、scenarios、`generate_script.py` 未着手。
- ☐ **AC-3 TTS 生成**: VOICEVOX / Open JTalk ラッパ、`synthesize_tts.py` 未着手。
- ☐ **AC-4 baseline 実行**: `run_long_dialogue.py`（JSONL/CSV ログ）未着手。
- ☐ **AC-5 KV ポリシー抽象**: `kv_policy.py`（Default/NoOp/SlidingWindow/Rotating）未着手。
- ☐ **AC-6 長文脈スモークテスト**: 5分音声の実走（「4分の崖」観測）未着手。
- ☐ **AC-7 再現性**: run-id 付き成果物保存の仕組み未着手。

> メモ: `moshi-internals.md` §6 の通り、AC-6 で baseline の「4分の崖」を観測してから
> 実際の KV 操作（AC-5 の中身）を入れる方針（CLAUDE.md「done の定義」/ spec §19）。

## いま進めていること（Epic #18: 理解支援システム）

claude.ai チャットから「Moshi の仕組み」「変更履歴」を pull で聞ける状態を作る。

- ☑ #19 `docs/moshi-internals.md`（仕組み解説 + 実験↔機構マップ）
- ☑ #20 `STATUS.md`（本ファイル）+ 再生成スクリプト `tools/gen_digest.py`
- ☑ #21 生成系サブエージェント（`progress-digest` / `moshi-explainer`）+ `docs/connect-claude-ai.md`

## 次の一手

1. Epic #18 を claude.ai 側で実地確認（GitHub コネクタ接続 → 質問が docs/STATUS を根拠に返るか）。
2. spec §16 の最初の実装プロンプトに沿って **AC-1 を満たす**（必須スクリプト/configs と
   `test_env.py` 等の雛形を TDD で追加）。
3. 以降 AC-2 → AC-5（プロバイダ / TTS / baseline 実行 / KV ポリシー抽象）。

## 関連

- 仕様: `spec.md`（§15 AC, §16/§17 実装プロンプト, §19 方針）
- 仕組み: `docs/moshi-internals.md`
- 連携手順: `docs/connect-claude-ai.md`
- Epic: #18 / 子: #19, #20, #21

<!-- AUTO:BEGIN -->
_自動生成: 2026-05-28 17:03 UTC （`tools/gen_digest.py`）_

### 直近の変更（`experiments/jmoshi_long_context` 配下のコミット）

- `38e77b7` Add J-Moshi long-context eval scaffolding with root-bind-mount devcontainer （2026-05-25）

<!-- AUTO:END -->
