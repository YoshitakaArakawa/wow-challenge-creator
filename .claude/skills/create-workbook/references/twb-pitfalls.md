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
- データソースの Pivot
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
- 期間の平均・標本標準偏差をどのシートでも同じ値で使うなら、表計算ではなく FIXED LOD で持つ。式の形は [calc-field-patterns.md](calc-field-patterns.md) の「ネストLOD」。
- formula 属性内の改行は `&#13;&#10;` で書く。生の改行は XML 上で空白に正規化され、`//` コメントが後続の式を飲み込む。パッチ JSON の `formula` に書いた改行は `apply-edits.ts` が変換するので、`rawXml` で `<column>` を直書きするときだけ自分で変換する。
- 線グラフのツールチップに週の日付を出すとき、同じ X 位置に2系列（今年・前年）が重なるなら `ATTR([Week])` は `*` になる。今年側は `MAX([Week])`、前年側は `MIN([Week])` を置く。

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
- 平均線と「平均 ± n 標準偏差」の帯は、アナリティクスペイン相当の参照線で描く。フィールドを追加せず、ペイン内のマークから計算される。今週を除外したいなら、今週を別ペインに分ける（判定フィールドを列に置く）。

```xml
<reference-line axis-column='[ds].[sum:Sales:qk]' enable-instant-analytics='false' fill-above='false' fill-below='false'
    formula='stdev' id='refband0' label-type='none' scope='per-pane' show-lines='both' type='sample'
    value-column='[ds].[sum:Sales:qk]' z-order='1'>
  <reference-line-value factor='-1' />
  <reference-line-value factor='1' />
</reference-line>
<reference-line axis-column='[ds].[sum:Sales:qk]' enable-instant-analytics='false' formula='average'
    id='refline0' label-type='none' scope='per-pane' value-column='[ds].[sum:Sales:qk]' z-order='2' />
```

- `type='sample'` が標本SD、`population` が母SD。帯の色は `<style-rule element='refband'>` の `fill-color`、線は `element='refline'` で指定する。
- 定数フィールドの値に線を引くなら、そのフィールドを詳細に置き、`formula='min'`・`scope='per-table'`・`value-column` に指定する。
- 離散ピルの「ヘッダーの表示」オフは `<style-rule element='label'>` に `<format attr='display' field='[ds].[none:X:nk]' value='false' />`（class / scope なし）で書く。`element='header'` の `display` は無視される。連続軸の非表示は `element='axis'` に `scope` 付きで書く。
- ビュー内の手動ソートは `<sort class='manual' column='…' direction='ASC'><dictionary><bucket>&quot;A&quot;</bucket>…</dictionary></sort>` を `<filter>` の後・`<aggregation>` の前に置く。XSD が要求する `<manual-sort>` は Desktop に拒否される（XSD と Desktop の食い違い。XSD 検証のエラーは無視してよい）。

## テキスト（formatted-text）

- 空白だけの `<run>` は捨てられる。項目間の空白は、隣の文字を含む run の中に書く。
- シートタイトルには `<[datasource].[attr:...]>` の形でフィールドを埋め込める。埋め込むフィールドは、いずれかのペインの詳細などビューに置く。
- 値が無いときは NULL ではなく空文字 `''` を返すようにする（ラベルに不要な表示を出さない）。

## ダッシュボード

- テキストだけのシートが `#####` の1行になるのは、ゾーンの高さが行数に足りないとき。行数 × 行の高さ＋余白以上の高さを取るか、高さ固定を外す。
- 固定サイズのゾーン高さの合計に、ゾーンごとの margin（上下）とコンテナの margin を足した値が、ダッシュボードの高さに収まるようにする。溢れた分は画面外に出て見えなくなる。
- `renderDashboard` は全シートを縦に等分するだけ。横並びや固定高さが要るレイアウトは、後処理で `<dashboards>` と `<windows>` を書く。
- パラメータ操作は `<zone type-v2='paramctrl' param='[Parameters].[Parameter 1]' mode='type_in' .../>` で置ける。

## データソースの Pivot

複数の指標（Sales / Profit など）を1組の計算でまかなうときは、テーブルの relation を `type='pivot'` の relation で包む。`<connection>` 内と `<object-graph>` 内の2か所に同じ relation がある。

```xml
<relation name='Pivot' type='pivot'>
  <columns>
    <column datatype='string' name='Pivot Field Names' />
    <column datatype='real' name='Pivot Field Values' />
  </columns>
  <tag name='Pivot Field Names'>
    <value name='[Profit]' />
    <value name='[Sales]' />
  </tag>
  <groups>
    <group name='Pivot Field Values'>
      <field name='[Orders].[Profit]' />
      <field name='[Orders].[Sales]' />
    </group>
  </groups>
  <relation connection='…' name='Orders' table='[Orders$]' type='table'>…</relation>
</relation>
```

- `<metadata-records>` から元の列（Sales / Profit）のレコードを外し、`Pivot Field Names`（string, `parent-name` は `[Pivot]`）と `Pivot Field Values`（real）のレコードを足す。
- 表示名は `<datasource>` 直下の `<column caption='Metric' name='[Pivot Field Names]' …/>` で付ける。計算式からは `[Pivot Field Names]` / `[Pivot Field Values]` で参照する。

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
