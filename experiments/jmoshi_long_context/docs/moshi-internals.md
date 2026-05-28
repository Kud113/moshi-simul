# Moshi / J-Moshi の仕組み（長文脈評価のための要点）

> このドキュメントは「Moshi の内部機構を半分くらいしか知らない」状態でも、本プロジェクト
> （`experiments/jmoshi_long_context/`）が **何を・なぜ** 測ろうとしているのかを掴むための
> オリエンテーション資料です。claude.ai のチャットから GitHub コネクタ経由で参照する前提で
> 日本語で書いています。一次情報は Moshi 論文と本リポジトリの `moshi/` 配下のソースです。
> 確証のない記述には **(仮説)** と明記します。

---

## 0. 30秒サマリ

- Moshi は **全二重（full-duplex）の音声対話モデル**。相手の音声を聞きながら同時に自分も
  喋れる（明示的なターン交代を持たない）。
- 音声は **Mimi** というニューラルコーデックで 12.5Hz の離散トークン列に変換され、
  Transformer がそのトークンを予測する。
- Transformer は2段構成：時間方向を司る **Temporal Transformer** と、1フレーム内の
  複数コードブックを司る **Depth Transformer（Depformer）**。
- 各フレームで、自分の発話に対応する **テキストトークン（内部独白 / inner monologue）** も
  同時に予測する。
- 長文脈の鍵は Temporal Transformer の **KVキャッシュ**。実装は **`RingKVCache`**（リング
  バッファ）で、保持できるステップ数に **上限（`context = 3000` フレーム ≒ 240秒 = 4分）**
  がある。**4分を超えると古い文脈が上書きされる**＝実質スライディングウィンドウ。

→ つまり **素の J-Moshi はすでに「window=3000 フレームのスライディング窓」で動いている**。
これが本プロジェクトの仮説検証にとって最重要の前提（§6 参照）。

---

## 1. Mimi（ニューラル音声コーデック）

- 役割：24kHz の生波形 ↔ 離散トークン列の相互変換。Moshi はこの離散トークンを言語モデル的に
  予測する。
- フレームレート **12.5Hz**：1 フレーム = **80ms**。
  - 出典：`moshi/moshi/models/loaders.py` の `sample_rate = 24000`, `frame_rate = 12.5`。
- 量子化：**残差ベクトル量子化（RVQ）** による複数コードブック。本構成では音声 **8 コードブック**
  （`n_q = 8`）、各コードブックの語彙サイズ `card = 2048`。
  - 出典：`moshi/moshi/models/lm.py` の `LMConfig`（`n_q`, `card`）, コーデック本体は
    `moshi/moshi/models/mimi.py` / `moshi/moshi/modules/seanet.py`。
- 第1コードブックは「意味（semantic）」寄り、残りは「音響（acoustic）」を表す設計
  **(仮説：論文記載の split-RVQ / 蒸留の理解に基づく。コード上の厳密対応は要確認)**。

長文脈との関係：Mimi 自体はフレーム単位のコーデックでストリーミング動作するため、
**長さによる劣化の主因にはなりにくい**。長文脈問題は次節の Transformer 側で起きる。

---

## 2. RQ-Transformer：Temporal と Depth の2段構成

Moshi の言語モデルは「時間方向」と「コードブック深さ方向」を分けて扱う **RQ-Transformer**。

### 2.1 Temporal Transformer（時間方向・大きい本体）
- 12.5Hz のフレーム列を **因果的（causal）** に処理する標準的な Transformer。
- 位置エンコーディングは **RoPE**（`max_period = 10000`）。
- 実装：`moshi/moshi/modules/transformer.py` の `StreamingTransformer` /
  `StreamingMultiheadAttention`。
- **ここが長文脈のボトルネック**。1 フレーム進むごとに KV キャッシュへ 1 ステップ積まれる。

### 2.2 Depth Transformer（Depformer・1フレーム内・小さい）
- 1 フレーム内の **複数コードブック（`dep_q = 8`）** を自己回帰的に予測する小型 Transformer。
- スコープは「そのフレーム内」だけなので、キャッシュは小さく一定。**長文脈の主因ではない**。
- 出典：`moshi/moshi/models/lm.py`（`dep_q`, depformer 関連）。

### 2.3 1フレームのトークン構成（概念図）
```
フレーム t (80ms)
  ├─ テキストトークン（内部独白, text_card=32000）
  ├─ Moshi 自身の音声 8 コードブック（Depformer が生成）
  └─ ユーザ音声 8 コードブック（入力ストリーム）
```
テキスト・意味・音響の間には**遅延（delay）**が挿入され因果性と品質を助ける
**(仮説：`lm.py` の delays 設定に対応。厳密値は要確認)**。

---

## 3. 全二重（full-duplex）= 複数ストリーム同時モデリング

- Moshi は **自分の音声ストリーム** と **ユーザの音声ストリーム** を各フレームで **同時に**
  扱う。これにより「聞きながら喋る」全二重が成立し、明示的なターン区切りや話者分離を持たない。
- 割り込み（相手が被せて喋る）も、ユーザストリームが常時モデルに流れ込むことで自然に扱える、
  というのが設計上の狙い。
- 本プロジェクトの `interruption_after_long_context` シナリオ（§5）は、まさにこの全二重の
  挙動が **長文脈で saturate した後でも維持されるか** を突く。

---

## 4. 内部独白（inner monologue）とテキストトークン

- Moshi は自分が喋る音声に対応する **テキストトークン列** を、音声に先行して予測する。
  これを **内部独白（inner monologue）** と呼ぶ。
- 効果：生成品質の足場になり、同時に**そのまま書き起こし（transcript）** として使える。
- 評価上のうれしさ：音声を聞き取らなくても、内部独白テキストを見れば
  「合言葉を覚えているか」「話題 B に移れたか」を**ログから判定**できる
  （spec §13 の `recall_success` 等の自動アノテーション化に有用）。

---

## 5. KVキャッシュと長文脈：ここが本丸

### 5.1 RingKVCache（リングバッファ）
- Temporal Transformer の KV キャッシュは **`RingKVCache`**（`moshi/moshi/modules/
  transformer.py`）。docstring に *"capacity: Maximum number of steps to keep around"* とある通り、
  **保持ステップ数に上限を持つリングバッファ**。
- 容量を超えると **最古のステップを上書き** する。＝ **暗黙のスライディングウィンドウ**。

### 5.2 コンテキスト上限 = 3000 フレーム = 4分
- `moshi/moshi/models/lm.py` の `LMConfig.context = 3000`。
- 12.5Hz 換算で **3000 / 12.5 = 240 秒 = 4 分**。
- したがって **5 分対話（300s = 3750 フレーム）は学習・キャッシュ上限を超える**。

### 5.3 予想される壊れ方（測りたいもの）
| 観点 | 予想 | 根拠 |
|---|---|---|
| メモリ | **頭打ち**（青天井ではない） | RingKVCache が容量上限で上書きするため (仮説) |
| RTF | おおむね **一定** | 1ステップの attention 計算量が window で頭打ち (仮説) |
| 初期情報の保持 | **4分超で喪失** | 古いステップがリングで上書きされ window 外に出る |
| 失敗の出方 | OOM ではなく **静かな文脈切り捨て** になりやすい | 上記より (仮説) |

> 重要：素朴な「KV が無限に伸びて OOM する」モデルとは異なり、Moshi は**最初から窓付き**。
> よって本プロジェクトの第一の問いは「**4分の窓を超えた瞬間に何が起きるか**」になる。

---

## 6. 実験 ↔ 機構 対応マップ

spec §8 の4シナリオが、Moshi のどの機構の限界を突くのかを対応づける。

| シナリオ | 突く機構 | 観測したい現象 | 主に効く KV/window 政策 |
|---|---|---|---|
| `long_monologue_5min` | Temporal Transformer の context=3000 窓 / RingKVCache | 4分超でメモリ頭打ち・RTF安定の確認、品質劣化の有無 | baseline でまず素の窓挙動を観測 |
| `long_context_recall` | **RingKVCache の上書き（窓外退避）** | 冒頭の合言葉が4分後に window 外へ → **recall 失敗**するか | sliding_window / rotating_kv の差が出る本命 |
| `interruption_after_long_context` | 全二重（ユーザストリーム）× 飽和した時間文脈 | 窓が埋まった後でも割り込みに正しく反応できるか | 直近重視の窓政策が有利か検証 |
| `topic_shift` | 時間文脈の **recency バイアス** | 話題 B に移れるか、A に引き戻されないか | 窓が新情報を優先する度合いを観測 |

含意：`baseline` は既に「window=3000 のスライディング窓」なので、`SlidingWindowPolicy` /
`RotatingKVPolicy`（spec §11）は **この内蔵窓に対する追加操作** として意味を持つ。
v0 ではまず baseline で「4分の崖」を観測し（AC-6）、崖が確認できてから実際の KV 操作を入れる
（CLAUDE.md「done の定義」/ spec §19）。

---

## 7. もっと知りたい時の入口（ソース）

| 知りたいこと | 見るファイル |
|---|---|
| 音声コーデック（Mimi） | `moshi/moshi/models/mimi.py`, `moshi/moshi/modules/seanet.py` |
| LM 全体の設定 | `moshi/moshi/models/lm.py`（`LMConfig`） |
| Temporal Transformer / Attention | `moshi/moshi/modules/transformer.py`（`StreamingTransformer`, `StreamingMultiheadAttention`） |
| **KVキャッシュ本体** | `moshi/moshi/modules/transformer.py`（`RingKVCache`） |
| ストリーミング状態の枠組み | `moshi/moshi/modules/streaming.py` |
| RoPE 位置エンコーディング | `moshi/moshi/modules/rope.py` |
| モデルロード（HFリポ・サンプルレート等） | `moshi/moshi/models/loaders.py` |

---

## 8. まだ未確認 / 要検証（正直ベース）

- split-RVQ における意味/音響の厳密なコードブック割り当て **(仮説)**。
- テキスト・意味・音響間の delay の厳密値 **(仮説：`lm.py` の delays を要確認)**。
- `context=3000` が J-Moshi 系チェックポイント（`nu-dialogue/j-moshi-ext`）でも同値か
  **(要確認：ロードした config を実機で確認すること)**。
- RTF・メモリが本当に頭打ちかは **AC-6 の実測で確認**（このドキュメントの予想を更新する）。

> 実測で分かったことは `STATUS.md` と本ファイル §5/§8 に随時反映する。
