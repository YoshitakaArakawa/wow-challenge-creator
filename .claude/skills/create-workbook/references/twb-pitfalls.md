---
purpose: 生成した TWB が Tableau Desktop で開けない・表示が崩れる典型原因と、それを避けるための規範
sources:
  - https://github.com/tableau/tableau-plugin
  - https://github.com/tableau/tableau-document-schemas
fetched_at: 2026-10-03
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
- データソースの差し替え（同梱 Excel への直接接続）
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
- 文字列を含む書式（例：`"▲ Above range by $"#,##0`、`0" outside range"`）は Cloud の描画で無視され、既定の書式で出る。文言を付けたいときは、文字列を返す計算にする。

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
- 表示用の文字列がそのまま色の値を兼ねているフィールド（例：`Yes ▲` / `No`）は、文言を変えると割り当てが外れる。式と `<bucket>` を同時に直す。
- 配色を差し替えるときに hex を TWB 全体で置換するなら、同じ hex が別の役割（例：前年の線と区切り線）に使われていないかを先に数える。重なっていれば、文脈（`<bucket>` やゾーンの書式）で役割ごとに分けてから置換する。

## マークとシェルフ

- 線グラフで、点ごとに値が変わるディメンション（週の日付など）を詳細に置かない。線が切れて点になる。ツールチップ用なら `ATTR`（`[attr:...]`）でツールチップに置く。
- 二重軸は `<rows>([A] + [B])</rows>` とし、`pane id='1'` を A、`pane id='2'` を B に対応させる。A が背面に描かれるので、帯（ガント）を A、主系列を B にする。
- ペインと軸の対応は、行の二重軸なら `y-axis-name`、列の二重軸（`<cols>([A] + [B])</cols>`）なら `x-axis-name` で書く。取り違えると両ペインに同じ書式が当たる。
- 同じメジャーを 2 回置いた二重軸は、2 つのペインを軸の名前で区別できない。2 本目は同じ値の別名の計算フィールドにする。
- 軸の同期は、ワークシートの `<style>` の `<style-rule element='axis'>` に、B のフィールドを指す `<encoding attr='space' class='0' field='[ds].[B]' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />` を置く。ペインの `<style>` に書いても同期されない。
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
- 色で分けた線の重なり順は、色の凡例の並び順で決まる。先頭の項目が最前面に描かれる。主役の線を前に出すには、色のフィールドに手動ソート（下記）を付けて先頭にする。
- マークのサイズ（`<format attr='size'>`）は小数で指定できる。Cloud の 2 倍描画で、線は 0.6 で約 7px、0.1 で約 3px。円はサイズの値にほぼ比例して直径が変わる（1.26 で 22px、1.0 で 18px）。
- 定数フィールドの値に線を引くなら、そのフィールドを詳細に置き、`formula='min'`・`scope='per-table'`・`value-column` に指定する。
- 見出しの文字の書式は `<style-rule element='header'>` に書く。`field` 指定（`<format attr='color' field='[ds].[none:X:nk]' value='…' />`）は、行見出しでも列見出しでも色・太さ・サイズが効く。列見出しを `scope='cols'` だけで書くと、棒のシートでは色・太字が効くが、テキストのマーク（KPI カード）の列見出しでは色が効かない。列見出しは `field` 指定で書く。
  - 列に不連続のピルを 2 つ重ねた見出しは、段ごとに `field` を変えて書式を分けられる（例：指標名は太字、その下の値は通常の太さで大きく）。
- 表の区切り線（`element='table-div'`）で行の間に線を出すには `div-level` を 1 にする。区切り線は見出しの段・列にもかかるので、タイルの間だけを区切りたいときはマークの枠線（viz-techniques.md）を使う。
- 離散ピルの「ヘッダーの表示」オフは `<style-rule element='label'>` に `<format attr='display' field='[ds].[none:X:nk]' value='false' />`（class / scope なし）で書く。`element='header'` の `display` は無視される。連続軸の非表示は `element='axis'` に `scope` 付きで書く。
- 行・列のフィールドラベル（シェルフに置いたフィールド名の見出し）を消すには、`<style-rule element='worksheet'>` に `<format attr='display-field-labels' scope='rows' value='false' />` と、同じ形の `scope='cols'` を書く。
- ビュー内の手動ソートは `<sort class='manual' column='…' direction='ASC'><dictionary><bucket>&quot;A&quot;</bucket>…</dictionary></sort>` を `<filter>` の後・`<aggregation>` の前に置く。XSD が要求する `<manual-sort>` は Desktop に拒否される（XSD と Desktop の食い違い。XSD 検証のエラーは無視してよい）。

## テキスト（formatted-text）

- 空白だけの `<run>` は捨てられる。項目間の空白は、隣の文字を含む run の中に書く。
- シートタイトルには `<[datasource].[attr:...]>` の形でフィールドを埋め込める。埋め込むフィールドは、いずれかのペインの詳細などビューに置く。
- 値が無いときは NULL ではなく空文字 `''` を返すようにする（ラベルに不要な表示を出さない）。
- 塗りつぶしの四角の記号（■ █）は Cloud の描画で「..」になり、同じ行の後ろの文字も消える。▲ ▼ · — は正しく出る。帯の見本のような凡例は、記号ではなく言葉で書く。
- パラメータの値をラベルに出すには、パラメータをテキストのマークに置き、ラベルの文面に埋め込む。計算フィールドは要らない。
  - マーク：`<text column='[Parameters].[Parameter 1]' />`
  - 文面：`<run><![CDATA[<[Parameters].[Parameter 1]>]]></run>`
  - 文面に埋め込むだけでテキストのマークに置かないと、Cloud の描画で値が空になる。
  - 表示の書式はパラメータの `<column>` の `default-format`（例：`*MMM d, yyyy`）で決まる。パラメータコントロールの表示も同じ書式になる。
  - パラメータを参照する文字列計算をワークシートの `<datasource-dependencies>` にだけ定義してラベルに使うと、シート全体が空白になる。計算はデータソースに定義する（SKILL.md「参加者が再現できる規模にする」）。
- テキストのマークは折り返さない。1 行がシートの幅を超えると、ラベル全体が `#####` になる。ゾーンの高さを足しても、セルの `wrap` を指定しても直らない。長くなりうる文は、式の中で `CHAR(10)` の改行を入れて行を分ける（例：`REPLACE(TRIM([文]), '. ', '.' + CHAR(10))`）。

## ダッシュボード

- シートにスクロールバーが出る、またはどのシートも `#####` になるときは、まずダッシュボードの `<window>` に Fit の指定（`<zoom type='entire-view' />`）があるかを確かめる（twb-skeleton-cheatsheet.md の「ウィンドウ」）。
- Fit を指定してもシート（テキスト表・テキストだけのシート）が `#####` になるのは、多くはダッシュボード上の表示の高さが足りないとき（次に多いのは幅）。直すときは、そのシートのゾーンの高さを足すか、ダッシュボード自体の高さを足す。高さの目安は行数 × 行の高さ＋余白。高さを足しても直らないときは、1 行が幅を超えていないかを見る（「テキスト」の折り返しの項）。
- 固定サイズのゾーン高さの合計に、ゾーンごとの margin（上下）とコンテナの margin を足した値が、ダッシュボードの高さに収まるようにする。溢れた分は画面外に出て見えなくなる。
- ゾーンの `fixed-size` は、外側のパディング（`margin-top` / `margin-bottom`）を除いた中身の高さで書く。Desktop のレイアウトペインの高さ欄は、パディング込みの値を表示する。
  - 例：高さ欄 30・上下のパディング 14 の空白は、`fixed-size='2'` と `margin-top` / `margin-bottom` の `14` で書く。`fixed-size='30'` と書くと 58px を占め、下のゾーンが押し出される。
- `renderDashboard` は全シートを縦に等分するだけ。横並びや固定高さが要るレイアウトは、後処理で `<dashboards>` と `<windows>` を書く。
- 縦の流れコンテナにテキストゾーンを足すときは、表のシート（KPI のテキスト表）の直前を避ける。その位置に足すと表が `#####` になり、ゾーンの大きさを変えても直らないことがある（原因は未特定）。チャートを並べた横コンテナの直後なら問題なく置ける。直前に置きたい短い文は、既存のテキストゾーン（段の見出しなど）の行として足す。
- 複数のゾーンを 1 枚の色の面（パネル）に載せるには、コンテナとその子ゾーンの `zone-style` に `background-color` を書き、中のシートの `<style-rule element='table'>` にも同じ `background-color` を書く。シート側に書かないと、シートの白が面の上に塗られる。
- パラメータ操作は `<zone type-v2='paramctrl' param='[Parameters].[Parameter 1]' mode='type_in' .../>` で置ける。

## データソースの差し替え（同梱 Excel への直接接続）

テンプレのデータソースは hyper 抽出を持ち、元の Excel への接続は作者のマシンのパスを指している。抽出の中身は抽出した時点のデータで、要件が指定する期間を含まないことがある。出題のデータを使うときは、Excel を `.twbx` に同梱し、抽出を外して直接接続にする。

1. 出題のデータ（`common/Sample - Superstore.xlsx`）を `refine/wb-build/Data/Superstore/` にコピーする。
2. `<named-connection>` の中の `<connection class='excel-direct'>` の `filename` を、`wb-build` からの相対パスに書き換える。
3. `<datasource>` の中の `<extract …>` から `</extract>` までを丸ごと削除する（`<folders-common>` の後、`<layout>` の前にある）。`<object-graph>` の中の `<properties context='extract'>…</properties>` も削除し、`<properties context=''>` だけを残す。
4. `refine/wb-build/Data/Downloads/` の hyper ファイルを取り除く。

```xml
<named-connection caption='Sample - Superstore' name='excel-direct.xxxx'>
  <connection class='excel-direct' cleaning='no' compat='no' dataRefreshTime=''
      filename='Data/Superstore/Sample - Superstore.xlsx' interpretationMode='0' password='' server='' validate='no' />
</named-connection>
```

- 差し替えられるのは、シート名（`Orders`）と列の構成がテンプレと同じ Excel だけ。`<relation table='[Orders$]'>` と `<columns>`、`<metadata-records>` はそのまま使う。列の構成が違うデータへの差し替えは対象外。
- Pivot（次節）は、この直接接続にしてから行う。

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

- `<metadata-records>` から元の列（Sales / Profit）のレコードを外し、`Pivot Field Names`（string）と `Pivot Field Values`（real）のレコードを足す。どちらも `parent-name` は `[Pivot]`、`object-id` は他の列と同じにする。他の列の `parent-name` は `[Orders]` のままでよい。

```xml
<metadata-record class='column'>
  <remote-name>Pivot Field Names</remote-name>
  <remote-type>129</remote-type>
  <local-name>[Pivot Field Names]</local-name>
  <parent-name>[Pivot]</parent-name>
  <remote-alias>Pivot Field Names</remote-alias>
  <ordinal>20</ordinal>
  <local-type>string</local-type>
  <aggregation>Count</aggregation>
  <contains-null>true</contains-null>
  <object-id>[Orders_xxxx]</object-id>
</metadata-record>
```

- テンプレの `0_raw` フォルダにある `[Sales]` / `[Profit]` の `folder-item` は、残したままでも動く。
- 表示名は `<datasource>` 直下の `<column caption='Metric' name='[Pivot Field Names]' …/>` で付ける。計算式からは `[Pivot Field Names]` / `[Pivot Field Values]` で参照する。

## 計算フィールドの整理（フォルダ）

- 計算フィールドは役割ごとのフォルダに入れる。データペインでの並び順を固定するため、フォルダ名は番号付きにする。
  - 例：`1_Shared`（複数の計算やシートから使う土台）／`2_Period`（期間の判定）／`3_Stats`（平均・SD・範囲）／`4_Answers`（Yes/No・位置・差）／`5_Display`（色・ラベルなど表示用）
  - `1_Shared` に入れる目安は、3 つ以上の計算から参照されるか、複数種のシートで直接使われること。
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
