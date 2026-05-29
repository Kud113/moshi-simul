# docs — 理解支援ドキュメント

claude.ai のチャットから GitHub コネクタ経由で読む前提の、日本語ドキュメント置き場です。

| ファイル | 内容 | 対応 Issue |
|---|---|---|
| [`moshi-internals.md`](./moshi-internals.md) | Moshi / J-Moshi の仕組み（Mimi / 全二重 / Temporal+Depth Transformer / 内部独白 / KVキャッシュ）と、4シナリオ ↔ 機構の対応マップ | #19 |
| [`connect-claude-ai.md`](./connect-claude-ai.md) | claude.ai のチャットからこのリポジトリに繋いで「仕組み・進捗」を質問する手順 | #21 |

進捗・変更のダイジェストは1つ上の階層 [`../STATUS.md`](../STATUS.md) にあります。

## 使い方（ざっくり）

- 「Moshi ってどう動くの？」 → `moshi-internals.md`
- 「今どこまで進んだ？最近何変えた？」 → `../STATUS.md`
- 「claude.ai からどうやって聞くの？」 → `connect-claude-ai.md`
