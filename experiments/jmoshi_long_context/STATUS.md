# STATUS — J-Moshi 長文脈評価ハーネス 進捗ダイジェスト

> claude.ai のチャットから「今どこまで進んだ？最近何を変えた？」に答えるための単一の真実源。
> 上半分（AC 進捗・次の一手）は手動メンテ、下半分の `AUTO:BEGIN/END` ブロックは
> `tools/gen_digest.py`（またはサブエージェント `progress-digest`）が git から自動生成します。

## 受け入れ条件（spec §15: AC-1 .. AC-7）

凡例: ☐ 未着手 / ◐ 進行中 / ☑ 完了

- ◐ **AC-1 リポジトリ整備**: `experiments/jmoshi_long_context/` と `spec.md` は存在。
  `pytest` は `tests/test_env.py` / `test_kv_policy.py`（main `#17`）と本 Epic の
  `test_docs.py` / `test_status.py` / `test_agents.py` を発見可能。
  ただし `run_long_dialogue.py` / `run_baseline.py` / `configs/*.yaml` / `input_generation/*` は未作成。
- ☐ **AC-2 入力生成**: Ollama / HF プロバイダ、scenarios、`generate_script.py` 未着手。
- ☐ **AC-3 TTS 生成**: VOICEVOX / Open JTalk ラッパ、`synthesize_tts.py` 未着手。
- ☐ **AC-4 baseline 実行**: `run_long_dialogue.py`（JSONL/CSV ログ）未着手。
- ◐ **AC-5 KV ポリシー抽象**: `kv_policy.py`（Default/NoOp/SlidingWindow/Rotating）と
  `get_policy()` レジストリは main に存在（`#17` / `b02ab52`、すべて v0 のプレースホルダ no-op）。
  ただし config（`configs/*.yaml`）からの選択と `run_long_dialogue.py` への配線が未整備。
- ☐ **AC-6 長文脈スモークテスト**: 5分音声の実走（「4分の崖」観測）未着手。
- ☐ **AC-7 再現性**: run-id 付き成果物保存の仕組み未着手。

> メモ: `moshi-internals.md` §6 の通り、AC-6 で baseline の「4分の崖」を観測してから
> 実際の KV 操作（AC-5 の中身）を入れる方針（CLAUDE.md「done の定義」/ spec §19）。

## いま進めていること（Epic #18: 理解支援システム）

claude.ai チャットから「Moshi の仕組み」「変更履歴」を pull で聞ける状態を作る。

- ☑ #19 `docs/moshi-internals.md`（仕組み解説 + 実験↔機構マップ）
- ☑ #20 `STATUS.md`（本ファイル）+ 再生成スクリプト `tools/gen_digest.py` + 「直近の変更（何を/なぜ）」節
- ☑ #21 生成系サブエージェント（`progress-digest` / `moshi-explainer`）+ `docs/connect-claude-ai.md`

→ いずれも PR #22 に集約（main 取り込み後 claude.ai 実地確認へ）。

## 次の一手

1. Epic #18 を claude.ai 側で実地確認（GitHub コネクタ接続 → 質問が docs/STATUS を根拠に返るか）。
2. spec §16 の最初の実装プロンプトに沿って **AC-1 を満たす**（必須スクリプト/configs と
   `test_env.py` 等の雛形を TDD で追加）。
3. 以降 AC-2 → AC-5（プロバイダ / TTS / baseline 実行 / KV ポリシー抽象）。

## 直近の変更（何を / なぜ）

> 「何を変えたか」のコミット粒度は下部 `AUTO:BEGIN/END` ブロックが git から自動生成。
> ここは人が「**なぜ**」と「**対象 PR / コミット範囲**」を残すための手動メモ。

- **PR #22 — Epic #18「理解支援システム」（対象範囲: `cae669b`..`e9f5372`, 子 Issue #19/#20/#21）**
  - 何を: `docs/moshi-internals.md`・`docs/connect-claude-ai.md`・`docs/README.md`・本 `STATUS.md`・
    `tools/gen_digest.py`・サブエージェント 2 種（`progress-digest` / `moshi-explainer`）・対応テスト 3 本を追加。
  - なぜ: claude.ai チャットが GitHub コネクタ経由（**pull 型**）で「Moshi の仕組み / 進捗」を
    リポジトリ内の日本語 Markdown を根拠に答えられるようにするため。コード本体は未変更（理解支援のみ）。
- **`#17` / `b02ab52` — 環境チェック + KV ポリシー抽象（AC-1, AC-5 の骨格）**
  - 何を: `kv_policy.py`（4 ポリシーのプレースホルダ + `get_policy()`）と `tests/test_env.py` /
    `tests/test_kv_policy.py` を追加。
  - なぜ: spec §11 の共通インターフェース（選択・呼び出し・ログ）を先に固めるため。
    実際の KV eviction は AC-6 で「4 分の崖」を観測してから（spec §19 / CLAUDE.md）。
  - 注: 本 PR #22 ブランチは `#17` マージ前から分岐しているため `kv_policy.py` を含まない。
    main へマージ後は両者が揃う。

## 関連

- 仕様: `spec.md`（§15 AC, §16/§17 実装プロンプト, §19 方針）
- 仕組み: `docs/moshi-internals.md`
- 連携手順: `docs/connect-claude-ai.md`
- Epic: #18 / 子: #19, #20, #21

<!-- AUTO:BEGIN -->
_自動生成: 2026-05-29 17:22 UTC （`tools/gen_digest.py`）_

### 直近の変更（`experiments/jmoshi_long_context` 配下のコミット）

- `e9f5372` Add claude.ai-readable understanding-aid: Moshi internals doc, STATUS digest, generator subagents （2026-05-28）
- `38e77b7` Add J-Moshi long-context eval scaffolding with root-bind-mount devcontainer （2026-05-25）

<!-- AUTO:END -->
