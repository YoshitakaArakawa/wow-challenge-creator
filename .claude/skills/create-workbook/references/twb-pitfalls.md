---
purpose: 生成した TWB が Tableau Desktop で開けない・表示が崩れる典型原因と、それを避けるための規範
sources:
  - https://github.com/tableau/tableau-plugin
  - https://github.com/tableau/tableau-document-schemas
fetched_at: 2026-10-01
source_last_known_update: 不明
note: create-workbook で rawXml・後処理スクリプトを使って TWB を組み立てるときの落とし穴集。XML の骨格は twb-skeleton-cheatsheet.md、式の書き方は calc-field-patterns.md が担当し、ここは「XSD を通っても Desktop で失敗するもの」と「見た目が崩れるもの」に絞る。
---

# TWB 生成の落とし穴

## 目次
- Desktop に拒否される属性
- 計算式
- 数値書式
- 色の割り当て
- マークとシェルフ
- テキスト（formatted-text）
- ダッシュボード
- 計算フィールドの整理（フォルダ）

## Desktop に拒否される属性

- 新しい属性は、テンプレと同じ `source-build` と `document-format-change-manifest` を持つ実ブックに現れるものだけを使う。
- manifest の機能フラグに依存する属性は、XSD 検証を通っても Desktop で "attribute is not declared" になる。
  - 例：パラメータ `<range>` の `period-type-v2`、`<reference-line>` の `tooltip-type`
- 属性名の綴り誤り（例：`class-`）は XSD 検証で検出できる。生成後は必ず XSD 検証を回す。

## 計算式

- アポストロフィを含む文字列リテラルは二重引用符で囲む。
  - 良：`"Within last year's range"`
  - 悪：`'Within last year's range'`（式がエラーになる）
- 式がエラーのフィールドを1つでも参照するシートは、ビューもタイトルも丸ごと空白になる。空白シートを見たら、まず参照先フィールドのエラーを疑う。
- 週の切り捨ては週の開始曜日を明示する：`DATETRUNC('week', [Order Date], 'sunday')`
- 期間の平均・標本標準偏差をどのシートでも同じ値で使うなら、表計算ではなく FIXED LOD で持つ。
  - 平均：`{FIXED : SUM(IF [In Period] THEN [Sales] END)} / n`
  - 二乗和：週合計 `{FIXED [Week] : SUM([Sales])}` に行の値を掛けて足すと、週合計の二乗和になる：`{FIXED : SUM(IF [In Period] THEN [Weekly Sales] * [Sales] END)}`
  - 標本SD：`SQRT((二乗和 - n * SQUARE(平均)) / (n - 1))`
  - 前提：期間内の全週にデータがある（欠けた週は 0 として扱われない）。
- formula 属性内の改行は `&#13;&#10;` で書く。生の改行は XML 上で空白に正規化され、`//` コメントが後続の式を飲み込む。`apply-edits.ts` は改行を変換しないので、コメントや改行を入れない。

## 数値書式

- 表示単位 K の書式（`c"$"#,##0.0,K`）は適用されず、値が1000倍の見た目になる。千単位表記は使わない。
- 動作確認済みの `default-format`：

| 用途 | 書式 |
|---|---|
| 通貨 | `c"$"#,##0;-"$"#,##0` |
| 符号付き通貨 | `*+$#,##0;-$#,##0` |
| 符号付き % | `*+0.0%;-0.0%;0.0%` |
| 日付 | `*MMM d, yyyy` |

- 符号付き通貨で `"$"` を引用符で囲むと、`+` と `$` の間で改行されることがある。

## 色の割り当て

- 離散フィールドの色の割り当ては、データソース直下の `<style>`（`<layout>` の直後）に書く。ワークシートの `<style>` に書いた割り当ては無視される。
- 同じデータソースに、そのフィールドの `<column-instance>` も宣言する。

```xml
<column-instance column='[Calculation_005]' derivation='None' name='[none:Calculation_005:nk]' pivot='key' type='nominal' />
<layout ... />
<style>
  <style-rule element='mark'>
    <encoding attr='color' field='[none:Calculation_005:nk]' type='palette'>
      <map to='#2a78d6'><bucket>true</bucket></map>
      <map to='#b3afa3'><bucket>false</bucket></map>
    </encoding>
  </style-rule>
</style>
```

- 文字列の値は `<bucket>&quot;This year&quot;</bucket>` のように `&quot;` で囲む。

## マークとシェルフ

- 線グラフで、点ごとに値が変わるディメンション（週の日付など）を詳細に置かない。線が切れて点になる。ツールチップ用なら `ATTR`（`[attr:...]`）でツールチップに置く。
- 二重軸は `<rows>([A] + [B])</rows>` とし、`pane id='1'` を A、`pane id='2'` を B に対応させる。A が背面に描かれるので、帯（ガント）を A、主系列を B にする。
- 軸の同期は B 側に `<encoding attr='space' ... fold='true' synchronized='true' type='space' />` を置く。
- 平均線の参照線は、定数を返すフィールドを詳細に置き、`formula='min'`・`scope='per-table'`・`value-column` にそのフィールドを指定する。

## テキスト（formatted-text）

- 空白だけの `<run>` は捨てられる。項目間の空白は、隣の文字を含む run の中に書く。
- シートタイトルには `<[datasource].[attr:...]>` の形でフィールドを埋め込める。埋め込むフィールドは、いずれかのペインの詳細などビューに置く。
- 値が無いときは NULL ではなく空文字 `''` を返すようにする（ラベルに不要な表示を出さない）。

## ダッシュボード

- テキストだけのシートが `#####` の1行になるのは、ゾーンの高さが行数に足りないとき。行数 × 行の高さ＋余白以上の高さを取るか、高さ固定を外す。
- 固定サイズのゾーン高さの合計に、ゾーンごとの margin（上下）とコンテナの margin を足した値が、ダッシュボードの高さに収まるようにする。溢れた分は画面外に出て見えなくなる。
- `renderDashboard` は全シートを縦に等分するだけ。横並びや固定高さが要るレイアウトは、後処理で `<dashboards>` と `<windows>` を書く。
- パラメータ操作は `<zone type-v2='paramctrl' param='[Parameters].[Parameter 1]' mode='type_in' .../>` で置ける。

## 計算フィールドの整理（フォルダ）

- 計算フィールドは役割ごとのフォルダに入れる。データペインでの並び順を固定するため、フォルダ名は番号付きにする。
  - 例：`1_Period`（期間の判定）／`2_Stats`（平均・SD・範囲）／`3_Answers`（Yes/No・位置・差）／`4_Labels`（表示用の文字列）／`5_Chart Helpers`（軸位置・帯・ラベル用）
- パッチ JSON の `calculatedFields[].folder` にフォルダ名を書けば、`apply-edits.ts` が `<folders-common>` に振り分ける。XML を直接書く場合の形は次のとおり。
- `<folders-common>` は `<datasource>` 直下に置く。テンプレに `0_raw` フォルダがある場合は同じ要素に追記する。
- `<folders-common>` は計算フィールドの `<column>` 群の後、`<layout>` の前に置く。

```xml
<folders-common>
  <folder name='0_raw'> ... </folder>
  <folder name='2_Stats'>
    <folder-item name='[Calculation_020]' type='field' />
  </folder>
</folders-common>
```

- フォルダと合わせて、キャプションの先頭を揃える（例：`Q1 ...`〜`Q4 ...`）と、同種のフィールドがフォルダ内で隣り合う。
