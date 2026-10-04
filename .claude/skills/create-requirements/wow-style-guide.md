---
purpose: WOW 要件ページ（Introduction / Requirements / Dataset）を書くときの規範
sources:
  - https://workout-wednesday.com/category/tableau/
fetched_at: 2026-10-04
note: workout-wednesday.com の実際の投稿の構成と、過去の出題で受けたレビューから抽出した規範。手順（いつ何を書くか）は SKILL.md 側にある
---

# WOW 要件ページ スタイルガイド

## 目次
- ページ構成
- Introduction の書き方
- Requirements の書き方
- Dataset の書き方
- タイトル
- テンプレート（英語版）
- HTML版（サイト掲載用）

## ページ構成

WOW の出題ページは Introduction → Requirements → Dataset の順に並ぶ。その後に Attribute / Share / Solution などサイト定型の節が続く。

- 要件文として書くのは Introduction・Requirements・Dataset の3節
- Hints の独立した節は通常ない。ヒントを出すなら Introduction か Requirements の該当行に添える

## Introduction の書き方

### 規範
- 英語版で 120 語以内を目安に、1〜2段落で書く
- 「なぜ今このチャレンジか」を作者自身の考えとして書く。製品の機能紹介や発表内容の要約を主役にしない
- 後半で、参加者が作るものを 1〜2 文で示す（箇条書きにしない）
- 読者が知らない前提（イベント名・独自の用語）は 1 文で補うか、使わない
- 他人の発言や発表を根拠にするときは、ユーザーの一次資料（メモ・書き起こし）に基づく。Web 検索の要約を引用のように書かない
- 締めは "Have fun with it!" のような定型の一言でよい

### 避けるべきこと
AI 生成感の出る書き方を避ける。

- em dash（`—`）でのつなぎ。ピリオドやコンマで区切る
- コロンで言い換える文が続く
- 自分で問いを立て、直後に自分で答える
- 宣伝口調（"powerful", "game-changing" など）
- 本文をまとめ直すだけの締めの一文
- 学習目標の箇条書きや、教科書的な文体

## Requirements の書き方

### 中心原則：画像から読めないことだけを書く

参加者は完成したダッシュボードを見ながら再現する。見れば分かることは "Match the formatting as closely as possible" に任せ、要件には見ても分からないことだけを書く。

| 書く（画像から読めない） | 書かない（画像で分かる・既定のまま） |
|---|---|
| ダッシュボードサイズ | チャートの種類・配置・並び順 |
| パラメータの選択肢と初期値 | 色・フォント・ラベルや凡例の有無と位置 |
| 期間・比較対象の定義 | ツール既定のままの設定（週の開始曜日など） |
| 判定・色分けの条件と、境界の扱い | 使うデータ（Dataset 節に書く） |
| 各数字が何を表すか | |
| 表示する要素の一覧（要素ごとに何を出すか） | |
| 制作上の制約（Web Authoring のみ、シート数の上限など） | |

### 書き方
- 肯定形で書く。「〜しない」型の要件は、するべきことに言い換えるか削る
  - 例：「平均に今週を含めない」→「今週の直前13週と比べる」
- 「何を」だけを書く。選んだ理由や意図は Introduction に回す
- 用語は 1 語 1 義で使う。Introduction と要件で同じ語を別の意味に使わない
- 閾値や範囲の境界がどちら側に入るかを書く。区分同士が重ならないようにする
- 計算式や Tableau の関数名・機能名を書かない。解き方は参加者に委ねる
- 関連する要件は親項目の下にネストしてまとめる（3段まで可）。子が 1 行しかない親は平らに戻す
- 節見出し（`### KPIカード` 等）で分割しない。まとまりはネストで作る

### 避けるべきこと
- 冗長な説明（「基準日を起点に過去14日間。Day -14からDay 0で途切れる」→「直近14日間」で十分）
- 他の要素から一目で読める情報を、別の要素やシートで繰り返させる要件（例：範囲外のタイルが濃い色と ▲ / ▼ で分かるのに、範囲外の件数も出させる）。参加者の手順が増えるだけで、ダッシュボードの答えは変わらない

悪い例（順に：既定のままの設定、否定形と理由の添え書き、解法ヒントと画像で分かる見た目）:

```markdown
- Weeks start on Sunday
- No value labels on the charts (this week's value is in the tile headers)
- Row 1 charts: bars for the previous 13 weeks with the range band (the Analytics pane is enough). Set this week's bar slightly apart
```

## Dataset の書き方

- データ名とリンクだけを書く。説明は付けても 1 文まで
- WOW 共通の Superstore ならデータ名だけでよい

## タイトル

形式: `#WOW{YYYY} W{N}: Can You {動詞}...?`（例: `Can You Build a KPI Trigger Monitor?`）

- 「Can you」で始まる疑問形が標準
- 作るものの性格が伝わる具体語を選ぶ。どの出題にも当てはまる汎用語（Performance Dashboard など）や製品名は避ける

## テンプレート（英語版）

構造の目安。要件の行数やネストは出題に合わせて変えてよい。

```markdown
# WOW{YYYY} W{N}: {Title}

## Introduction

{1-2 paragraphs, about 120 words: why this challenge now, then what participants will build}

## Requirements

- Dashboard size: {width} x {height}
- {Parameter: choices and default}
- {Definition or rule}
  - {Detail}
- Elements to show:
  - {Element}
    - {What it shows}
- Match the tooltips and formatting as closely as possible

## Dataset

{Data name and link}
```

日本語版のテンプレートは不要。出題者との会話の中で自然に生成する。

## HTML版（サイト掲載用）

英語版MDファイルの末尾に、`<!-- HTML VERSION (for site posting)` で始まる HTML コメントとして、サイト掲載用の HTML 版を埋め込む。MDプレビューには表示されず、ファイルを開けばコピペできる。

- 見出しは `<h2>`、段落は `<p>`、要件は `<ul>` / `<li>` で書く。ネストした箇条書きは、親の `<li>` の中に `<ul>` を入れる
- MD版の内容と同期させること（MD側を修正したらHTML版も更新する）
- 別ファイルとしては作成しない（1ファイルで管理）
- ファイル名やキーワードは、MD版でバッククォートで囲んでいても、HTML版では `<code>` タグを使わずプレーンテキストで記述する（掲載先サイトのスタイルと干渉するため）
