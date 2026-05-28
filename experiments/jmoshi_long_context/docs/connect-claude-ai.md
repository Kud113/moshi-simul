# claude.ai チャットからこのプロジェクトに「連携・質問」する手順

このプロジェクトの理解支援は **claude.ai（Web/アプリのチャット。Claude Code CLI ではない）**
を「聞く側」に置く設計です。claude.ai に **GitHub コネクタ** でこのリポジトリを繋ぎ、
リポジトリ内の日本語 Markdown（`docs/` と `STATUS.md`）を根拠に答えてもらいます。

> 方式: **GitHub コネクタ（pull 型）** / 通知: **pull 型のみ**
> （claude.ai は「聞けば答える」型で、自発的な push 通知は行いません）

---

## 1. 前提

- claude.ai のアカウント（コネクタ/連携が使えるプラン）。
- このリポジトリ `Kud113/moshi-simul` に閲覧権限があること。

## 2. GitHub コネクタを有効化する（初回のみ）

1. claude.ai を開き、設定（Settings）→ **Connectors / 連携** を開く。
2. **GitHub** を選び、認可（OAuth）。組織リポジトリの場合は管理者承認が要ることがある。
3. アクセス対象に `Kud113/moshi-simul`（少なくとも参照）を含める。

> 補足: 連携の入口・名称は claude.ai 側の更新で変わることがあります。
> 「GitHub を接続できる場所」を設定内で探してください。

## 3. プロジェクト（任意）にまとめると安定

- claude.ai の **Projects** を1つ作り、GitHub コネクタでこのリポジトリを紐付ける。
- Project のカスタム指示に、例えば次を入れておくと回答が安定します:
  - 「`experiments/jmoshi_long_context/docs/moshi-internals.md` と
    `experiments/jmoshi_long_context/STATUS.md` を一次情報として優先的に参照すること。
    日本語で答えること。推測には『(仮説)』を付けること。」

## 4. 実際に聞く（pull 型）

チャットで例えば次のように聞きます:

- 「**Moshi の仕組みを教えて**」
  → `docs/moshi-internals.md` を根拠に、Mimi / 全二重 / Temporal+Depth / KVキャッシュを説明。
- 「**最近の変更点と、今どの AC まで終わってる？**」
  → `STATUS.md` を根拠に、AC-1..7 の進捗と直近コミットを要約。
- 「**5分対話で何が壊れそう？なぜ？**」
  → `moshi-internals.md` §5/§6 を根拠に「4分の窓（context=3000）超過」を説明。

## 5. 最新さを保つ（重要）

claude.ai は **その時点でリポジトリにある Markdown** を読みます。情報が古いと感じたら、
**生成側（Claude Code）で docs / STATUS.md を更新してコミット**してください:

- `STATUS.md` の更新 → サブエージェント **`progress-digest`**、または
  `python experiments/jmoshi_long_context/tools/gen_digest.py`
- `docs/moshi-internals.md` の加筆/検証 → サブエージェント **`moshi-explainer`**

更新を push したあと、claude.ai 側で再度質問すれば新しい内容が反映されます。

---

## よくある質問

- **Q. claude.ai から自動で通知してほしい。**
  A. claude.ai は pull 型で、自発 push 通知はしません。通知が欲しい場合は将来の拡張として
  「重要イベントを PR コメントに出す（GitHub 通知で気づく）」を検討します（本 v1 ではスコープ外）。
- **Q. リアルタイムの実験ステータス（GPU/RTF）も聞きたい。**
  A. それにはリモート MCP コネクタが必要で、公開 HTTPS + OAuth が要るため現状スコープ外です
  （Epic #18 のスコープ外に記載）。まずは `STATUS.md` を最新化する運用で代替します。
