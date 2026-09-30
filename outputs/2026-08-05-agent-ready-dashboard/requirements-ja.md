# WOW2026 W31: Can You Build an Agent-Ready Dashboard?

公開済みVizから逆算した要件文（日本語版）。難易度: 初級。

## Introduction

Tableau MCPサーバーの実験的なフォークを動かしていて、ダッシュボードをAIチャットの中に住まわせようとしている。いちばん面白いのはViz状態のスナップショットだ。埋め込んだダッシュボードをフィルターすると、いま何を見ているかがモデルに伝わり、モデルはその裏のデータソースへクエリを投げられる。ダッシュボードが会話の終着点ではなく、自分とエージェントが一緒に眺めるものになる。

その場所に置くダッシュボードは、小さく、そして自力で説明できなければならない。会話の途中に現れるので、案内してくれる人が誰もいないからだ。というわけで今週は、モバイルに近いサイズでひとつ作ってみよう。あわせて、新しく使えるようになったTableau Publicのパブリッシュ済みデータソースも試す。これに接続できるのはブラウザからだけなので、今回は最後までWeb編集で進めることになり、Tableau Desktopは閉じたまま。カードの幅を決めるのはチャットアプリ側なので、下のサイズは固定値ではなくレンジにしてある。

## Requirements

- 準備
  - ダッシュボードサイズ: レンジ。最小 650 x 800、最大 750 x 900
  - Tableau PublicのWeb編集だけで作る。Tableau Desktopは使わない
  - パブリッシュ済みデータソース Sample Superstore 2026.2 に接続する。ファイルのアップロードは不可
  - シート5枚
- コントロール
  - 上部に Year Month、Region、Segment の単一選択ドロップダウンを横並びで
  - パラメーター1つ。`Selected Measure`、Sales / Profit / Profit Ratio のリスト、初期値は Profit Ratio
- ビュー
  - KPI行に Sales、Profit、Profit Ratio。指標名を上、値を下に
  - サブカテゴリ別に選択中の指標を横棒で、降順ソート。負の値が負として読める配色にする
  - 棒の値はグラフ右側の固定幅の列に置き、全行で右端を揃える
- 仕上げ
  - KPI行とパラメーターコントロールの背後に薄いグレーの帯
  - ツールチップは単体で意味が通るように。サブカテゴリ名、選択中の指標名、値
  - Match the tooltips and formatting as closely as possible

---

## 実装仕様（内部用・出題には含めない）

公開済みTWBXの解析結果。解答例の検証と、Hintsを書くときの参照用。

### データソース

`Sample Superstore 2026.2`（接続クラス `sqlproxy`、id `SampleSuperstore2026_2`）。Tableau Public上のパブリッシュ済みデータソース。TWBXは12KBで、抽出を同梱していない。

### パラメーターと計算フィールド

| 名前 | 内容 |
|---|---|
| `Selected Measure`（パラメーター） | integer / list。1=Sales, 2=Profit, 3=Profit Ratio。既定 3 |
| `Profit Ratio` | `SUM([Profit])/SUM([Sales])`、書式 `p0.0%` |
| `Selected Measure`（計算） | `CASE [Selected Measure] WHEN 1 THEN SUM(Sales) WHEN 2 THEN SUM(Profit) WHEN 3 THEN [Profit Ratio] END` |

通貨書式は `"$"#,##0;-"$"#,##0`。

### ダッシュボード

`sizing-mode='range'`、`minwidth=650 minheight=800`、`maxwidth=750 maxheight=900`。全オブジェクトがタイル配置で、浮動は使っていない。外周パディング20、ブランク区切りは12px固定。

上から順に:

1. テキスト: `WOW2026 W31`（15pt）+ `Can You Build an Agent-Ready Dashboard?`（Tableau Bold 20pt）、文字色 `#1b1b1b`
2. ブランク 12px
3. 水平コンテナ（背景 `#f5f5f5`、均等配置）: Year Month / Region / Segment のドロップダウン3つ
4. KPI行: 高さ80px固定の水平コンテナ、Sales / Profit / Profit Ratio の3シートを均等配置、タイトル非表示
5. ブランク 12px
6. 水平コンテナ（背景 `#f5f5f5`、均等配置）: パラメーターコントロール（compact表示、カスタムタイトル `Select a KPI to Show` を斜体）を左1/3に置き、残り2枠はブランク
7. 水平コンテナ: `KPI by SubCat`（幅可変、最小245）+ `KPI by SubCat (Label)`（幅92px固定）
8. テキスト: `Data: Sample Superstore 2026.2`、右揃え

### シート

**Sales / Profit / Profit Ratio**（KPI用、3枚）
テキストマーク1個。カスタムラベルが2行構成で、1行目に指標名（12pt）、2行目に値（Tableau Bold 15pt）。ツールチップは `Sales:` を `#757575` で置き、値を太字。

**KPI by SubCat**
行 = Sub-Category、列 = Selected Measure、色 = Selected Measure。Selected Measure の降順ソート。行ヘッダー幅145、フォント12、行の項目ラベル非表示。色はパレット指定が保存されていないため、既定の発散カラー（オレンジ - ブルー）。

**KPI by SubCat (Label)**
行 = Sub-Category、列 = `MIN(-1.0)`。軸は最大値 -1.0 で固定し、軸タイトルは空白1文字。テキスト = Selected Measure。行ヘッダーは非表示。グリッド線とゼロラインをオフ。

両シートのツールチップは共通で、1行目にサブカテゴリ名（太字）、2行目に `<Selected Measure>:` を `#757575`、タブ区切りで値を太字。

### 気づいた点（要修正候補）

- 棒グラフの軸タイトルが `Profit Ratio` の**固定文字列**として保存されている。パラメーターを Sales / Profit に切り替えても軸タイトルは Profit Ratio のまま。動的にするか、軸タイトル自体を消すかの判断が要る
- ラベル列の数値が `0.460` のように生の実数で出ている。KPI行の Profit Ratio は `7.5%` と%表示なので、同じ指標の表示形式が2箇所で食い違っている
- 出題タイトルに Mobile の語がない。埋め込み幅が主題なので現状のままで整合するが、要件の1行目でレンジサイズを明示しているので参加者には伝わる

### 事前確認

- 直近3回（W30 ラダーチャート、W29 会計カレンダー、W28 パレート）とテーマの被りなし。20260805確認
- 類似の過去出題は WOW2020 W43 Mobile Dashboard Challenge（Luke Stanke）。あちらはKPIタップで棒グラフを開閉する構成で、モバイル実機が前提。本作はAIチャット埋め込み幅・Web編集限定・公開データソースの3点で異なる
- 幅750px以下の根拠は、別リポジトリ `tableau-public-mcp-app` の `docs/chatgpt-host-notes.md`。ChatGPTインラインカードの実測で20260803に約768px、20260804は非再現
