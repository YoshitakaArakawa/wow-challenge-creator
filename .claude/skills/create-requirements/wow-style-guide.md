# WOW 要件ページ スタイルガイド

workout-wednesday.com の実際の投稿を分析して策定。要件文作成時に必ず参照すること。

---

## ページ構成

WOWの要件ページは **Introduction** と **Requirements** の2セクションで構成される。
Data、Hints、参考リンク等はサイト上の定型要素として別途存在するため、要件文としては上記2つだけを書く。

---

## Introduction の書き方

### トーン
- フレンドリーでカジュアル。堅すぎない
- 「なぜこのチャレンジを作ったか」「何にインスパイアされたか」を1〜2段落で
- 参加者が学べることを自然に伝える（箇条書きではなく文章で）

### よくあるパターン
- 個人的な動機やエピソードから入る（「〜に出会って面白いと思った」「〜が気になっていた」）
- 技術的な背景を簡潔に説明する
- 難易度への言及（「初めてのチャレンジにちょうどいい」「少し歯ごたえがあるかも」など、カジュアルに）

### 避けるべきこと
- 学習目標を箇条書きで列挙する（論文風になる）
- 過度に説明的・教科書的な文体
- em dash（`—`）をつなぎに使う（AI生成感が出るため。ピリオドやコンマで区切る）

---

## Requirements の書き方

### 形式
- **フラットな箇条書き**（サブセクションに分割しない）
- 1行1要件で簡潔に
- ネストは1段階まで（選択肢の列挙など）

### よく記載される項目
- ダッシュボードサイズ（必須）
- シート数（必須）
- パラメータの仕様（名前、型）
- 何を表示するか（「Profit Ratioを表示する」）
- チャートの構成要素（線の本数、比較対象など）
- 色分けやラベルの条件
- 「Match the tooltips and formatting as closely as possible」（定型文）

### 書き方のルール
- **「何を」は書く、「どう計算するか」は書かない** — 計算式（`SUM(Profit)/SUM(Sales)`等）は参加者に委ねる
- **目的や意図は簡潔に添える** — 「〜を判断するために」程度。長い説明は不要
- 技術用語は適度に使う。過剰な説明は不要（WOW参加者はTableauユーザー）

### 避けるべきこと
- サブセクション見出し（`### KPIカード` `### トレンドライン` 等）で分割する
- 計算式やTableau関数名を明示する
- 冗長な説明（「基準日を起点に過去14日間。Day -14からDay 0で途切れる」→ 「直近14日間」で十分）

---

## タイトル

形式: `#WOW{YYYY} W{N}: Can You {動詞}...?`

例:
- `Can You Build a KPI Trigger Monitor?`
- `Can you create a dynamic moving average?`
- `Can you create a fake Viz in Tooltip?`

「Can you」で始まる疑問形が標準。

---

## テンプレート（英語版）

```markdown
# WOW{YYYY} W{N}: {Title}

## Introduction

{1-2 paragraphs: Why this challenge? What inspired it? What will participants learn?}

## Requirements

- Dashboard size: {width} x {height}
- {N} sheet(s)
- {Requirement 1}
- {Requirement 2}
- {Requirement 3}
- Match the tooltips and formatting as closely as possible
```

日本語版のテンプレートは不要。出題者との会話の中で自然に生成する。

---

## HTML版（サイト掲載用）

英語版MDファイルの末尾に、HTMLコメントとしてサイト掲載用のHTML版を埋め込む。MDプレビューには表示されず、ファイルを開けばコピペできる。

```markdown
<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>...</p>

<h2>Requirements</h2>
<ul>
<li>...</li>
</ul>

-->
```

- MD版の内容と同期させること（MD側を修正したらHTML版も更新する）
- 別ファイルとしては作成しない（1ファイルで管理）
- ファイル名やキーワードは、MD版でバッククォートで囲んでいても、HTML版では `<code>` タグを使わずプレーンテキストで記述する（掲載先サイトのスタイルと干渉するため）

