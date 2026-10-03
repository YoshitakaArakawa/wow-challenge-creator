---
purpose: 少ない手順で見た目が大きく良くなる Tableau の定石と、その TWB での書き方
sources:
  - https://note.com/tabjo/m/ma0d9786ff888
  - https://www.flerlagetwins.com/2020/03/simple-steps-for-better-design.html
  - https://www.flerlagetwins.com/2026/02/ten-tableau-tips-table-of-contents.html
  - https://www.vizwiz.com/p/tips.html
  - https://help.tableau.com/current/pro/desktop/en-us/reference_lines.htm
  - https://help.tableau.com/current/pro/desktop/ja-jp/annotations_marklabels_showhideworksheet.htm
fetched_at: 2026-10-03
source_last_known_update: 不明
note: 日本語コミュニティ（Tableau 女子会、個人 note、企業ブログ）と英語圏（Flerlage Twins、VizWiz、Tableau Help）で繰り返し勧められる技のうち、手数が少なく計算が 0〜1 本で済むものに絞る。計算を多く使う自作チャート（Sankey、donut、waterfall など）は扱わない。XML の基本的な落とし穴（二重軸の同期、参照線の書式、色の割り当て）は twb-pitfalls.md が担当し、ここでは重複させない。
---

# 見た目を良くする軽量テクニック

## 目次
- 使い方
- A：既定で使う定石
- B：場面に応じて使う定石
- 実証済みの XML
- 対象外にした技

## 使い方

- 見た目の課題（ラベルの重なり、色の多さ、強調点が分からない等）に当たったら、計算や工程を足す前にこの一覧から選ぶ。
- 「XML 実証済み」は、Cloud の描画で効くことを確かめた書き方が「実証済みの XML」にある。
- 「XML 未実証」は、作り方の要点だけが確かな情報。TWB に書くときは refine ループで描画を確かめ、効いた書き方をこのファイルに追記する。推測で書いて効かなければ、GitHub のコード検索で Desktop が保存した `.twb` の書き方を探す。
- 手数は Tableau Desktop 上の操作数の目安。

## A：既定で使う定石

日本語・英語の両方の情報源で繰り返し勧められている。

| 技 | 解決すること | 作り方の要点 | 手数 | XML |
|---|---|---|---|---|
| 詳細に置いた別メジャーで参照線・帯 | 目標・前年・平均との差を一目で示す | 基準のメジャーを詳細に置き、参照線・帯の値にそのメジャーを指定する。基準が NULL の点は計算から外れる | 3、計算 0 | 実証済み |
| ラベルの表示条件（最新・線端・最小/最大） | 全点ラベルの騒がしさをなくす。線端の名前で凡例を省く | ラベルの「マークにラベルを付ける」で条件を選ぶ | 1〜2、計算 0 | 実証済み |
| ラベルの配置・向き | 重なり・はみ出し・縦書き化を防ぐ | ラベルの「配置」で水平・垂直・向きを設定する | 1〜2、計算 0 | 実証済み |
| `MIN(1.0)` のダミー軸（色付きタイル・KPI 枠） | セルを色で埋める。メジャーなしで枠や置き場を作る | 列に `MIN(1.0)` を置いて棒にし、軸を 0〜1 に固定して隠す。色とラベルに答えを置く | 3〜4、短い計算 1 | 実証済み |
| 二重軸で点を重ねる（最終点・強調点・ロリポップ） | 標準マーカーでは強調点だけ大きさ・色を変えられない | 2 本目の軸に「強調したい点だけ値を持つ」計算を置いて円にし、軸を同期する | 5、計算 0〜1 | 実証済み |
| Bar in Bar | 実績と目標・前年を省スペースで直接比べる | 棒 2 本を二重軸にして同期し、前面の棒を細くする | 4、計算 0 | 実証済み |
| ノイズ除去 | グリッド・ゼロ線・不要なヘッダーがデータの邪魔をする | 線をオフ、ヘッダーの表示を外す、棒の軸は 0 起点 | 1〜3、計算 0 | 実証済み（twb-pitfalls.md） |
| 強調色＋グレー | 色が多すぎて焦点がぼける | 主役だけ色、比較対象はグレー。重なるなら不透明度を下げる | 2〜3、計算 0〜1 | 実証済み（色の割り当て） |
| 正負で分けるカスタム数値書式（▲▼、+/−） | 増減の向きを計算なしで示す | 書式を「正;負;ゼロ」で書き分ける | 1〜2、計算 0 | 実証済み（twb-pitfalls.md） |
| BAN / KPI カード | 最重要の数値を即座に読ませる | テキストマークで大きな数値、比較を小さく併記する | 3、計算 0〜2 | 実証済み |
| コンテナ・余白・均等配分 | 要素が詰まる、まとまりが見えない | 縦横コンテナで「均等に配分」、余白をそろえる | 3〜5、計算 0 | 実証済み（twb-pitfalls.md） |
| 最新期の手前で止まる平均線 | アナリティクスの平均線が最新期のペインにも引かれる | 最新期だけ NULL を返すシート専用の計算を詳細に置き、平均線をその値のペイン平均にする | 3、計算 0（アドホック） | 実証済み |

## B：場面に応じて使う定石

片方の情報源で勧められているか、用途が限られる。

| 技 | 解決すること | 作り方の要点 | 手数 | XML |
|---|---|---|---|---|
| 発散型パレットの中心を基準値に合わせる | 良い/悪いの境目を色で正しく示す | 色の編集の詳細で中心を 0 や平均にする | 2〜3、計算 0〜1 | 実証済み |
| 動的タイトル・タイトル内の色付き文字で凡例を代替 | 凡例を省き、選択中の条件を伝える | タイトルにパラメーターやフィールドを挿入し、マークと同じ色の文字で書く | 2〜3、計算 0 | 実証済み |
| ヘッダー・軸を上部に表示 | 縦長のビューでラベルが下に行く | 表のレイアウトの詳細で「最下部に表示」を外す | 1、計算 0 | 未実証 |
| 最大値×110% の見えない参照線 | 最大値のラベルが上端で見切れる | 分布の参照線を最大の 110% に置き、線とラベルを消す | 3〜4、計算 0 | 実証済み |
| 参照線のラベルを棒の内側先端に置く | 通常のラベルは軸を伸ばしてしまう | セルごとの参照線のラベルを白・左揃えにし、線を透明にする | 4、計算 0 | 実証済み |
| 二重軸の片側をラベル専用にする | 積み上げで合計だけ、最新値だけを出す | 同じ値の別名の計算を 2 本目の軸に置き、色を外してラベルを付け、マークを透明にする | 5、短い計算 1 | 実証済み |
| 前年を薄い面、今年を線 | 2 期間の主役と背景を分ける | 前年を面か棒にして不透明度 10〜40%、今年を線にする | 4〜5、計算 0〜1 | 実証済み |
| 箇条グラフ（Bullet graph） | 実績と目標を省スペースで比べる | 実績を列、目標を詳細に置き、参照線と分布帯を足す | 3〜4、計算 0 | 実証済み |
| ツールヒントの整形 | ホバー時の情報過多 | 不要項目を消し、太字と単位で整える | 1〜2、計算 0 | 未実証 |
| マークの枠線 | 強調点や色付きタイルの輪郭がぼける。タイルの境目が見えない | 色の「枠線」で線の色を指定する。強調点は線と同じ色、タイルは白 | 1、計算 0 | 実証済み |
| 主役の線を前面に | 比較の線が主役の線の上に重なる | 色の凡例で主役の項目を先頭に並べ替える | 1、計算 0 | 実証済み（twb-pitfalls.md） |
| 答えのパネル | 画面のどこが結論か分からない | 結論のまとまり（見出しとタイル）を入れたコンテナに淡い背景色を付ける | 2、計算 0 | 実証済み（twb-pitfalls.md） |

ハイライト表（四角マークにメジャーを色とラベル）は広く勧められるが、生成した TWB では四角のサイズ指定でセルが埋まりきらない。色付きタイルは `MIN(1.0)` のダミー軸で作る。

## 実証済みの XML

`[ds]` はデータソース名（`federated.xxxx`）の省略。

### 詳細に置いた別メジャーで参照線・帯

軸のメジャー（`axis-column`）と計算に使うメジャー（`value-column`）を別にできる。`value-column` のメジャーをペインの `<lod>` に置く。基準が NULL の点（例：今年の点に対する前年の値）は平均・標準偏差の計算から外れる。

```xml
<lod column='[ds].[usr:Last Year Value:qk]' />
...
<reference-line axis-column='[ds].[sum:Value:qk]' value-column='[ds].[usr:Last Year Value:qk]'
    formula='stdev' type='sample' id='refband0' scope='per-pane' show-lines='both' label-type='none'
    enable-instant-analytics='false' fill-above='false' fill-below='false' z-order='1'>
  <reference-line-value factor='-1' />
  <reference-line-value factor='1' />
</reference-line>
```

### ラベルの配置・向き

ペインの `<style>` の `element='cell'` に書く。`element='mark'` に書いても効かない。`text-orientation` は `0` が横書き。

```xml
<pane ...>
  ...
  <style>
    <style-rule element='cell'>
      <format attr='text-orientation' value='0' />
      <format attr='text-align' value='left' />     <!-- マークの左側に置く -->
      <format attr='vertical-align' value='top' />  <!-- マークの上側に置く -->
    </style-rule>
    <style-rule element='mark'>
      <format attr='mark-labels-show' value='true' />
    </style-rule>
  </style>
</pane>
```

ラベルはペインの境界で切られる。列に離散フィールドを置いて今週などを別ペインに分けると、1 本幅のペインのラベルは配置を変えても切れる。そのときはラベルを諦めるか、値を別の場所（KPI など）に出す。

### `MIN(1.0)` のダミー軸で色付きタイル

アドホック計算はワークシートの `<datasource-dependencies>` にだけ置く。データソースの計算フィールドは増えない。

小数の `MIN(1.0)`（`datatype='real'`）を使う。軸範囲を細かく調整できる。整数の `min(1)` でも同じ見た目になる。

```xml
<!-- worksheet の datasource-dependencies -->
<column caption='min(1.0)' datatype='real' name='[Calculation_900]' role='measure' type='quantitative'>
  <calculation class='tableau' formula='min(1.0)' />
</column>
<column-instance column='[Calculation_900]' derivation='User' name='[usr:Calculation_900:qk]' pivot='key' type='quantitative' />

<!-- 表：行 = 問い、列 = 指標 / ダミー軸 -->
<cols>([ds].[none:Metric:nk] / [ds].[usr:Calculation_900:qk])</cols>

<!-- 軸を 0〜1 に固定して隠す（worksheet の style） -->
<style-rule element='axis'>
  <encoding attr='space' class='0' field='[ds].[usr:Calculation_900:qk]' field-type='quantitative'
      min='0' max='1' range-type='fixed' scope='cols' type='space' />
  <format attr='display' class='0' field='[ds].[usr:Calculation_900:qk]' scope='cols' value='false' />
  <format attr='title' class='0' field='[ds].[usr:Calculation_900:qk]' scope='cols' value='' />
</style-rule>

<!-- ラベルをタイルの中央に（worksheet の style。無いと棒の右端に寄る） -->
<style-rule element='cell'><format attr='text-align' value='center' /></style-rule>

<!-- ペイン：棒を最大の太さで -->
<mark class='Bar' />
<mark-sizing mark-sizing-setting='marks-scaling-off' />
<!-- encodings に color と text（答えのフィールド） -->
<style><style-rule element='mark'><format attr='size' value='10' /></style-rule></style>
```

色はデータソース直下の色の割り当てで指定する（twb-pitfalls.md の「色の割り当て」）。

### 二重軸で最終点を強調する（Sparkline）

1 本目の軸に線（期間を色で分ければ、今年と前年を 1 本の軸にまとめられる）、2 本目の軸に「最終点だけ値を持つ」計算を円で置く。最終点の計算は表計算（`LAST()=0`）でも、行レベルの条件（`SUM(IF [Is This Week] THEN [Value] END)`）でもよい。軸の同期と非表示は twb-pitfalls.md の「マークとシェルフ」に従う。

```xml
<rows>([ds].[sum:Value:qk] + [ds].[usr:This Week Value:qk])</rows>
...
<pane id='1' y-axis-name='[ds].[sum:Value:qk]'>
  <mark class='Line' />
  <encodings><color column='[ds].[none:Period:nk]' /> ... </encodings>
</pane>
<pane id='2' y-axis-name='[ds].[usr:This Week Value:qk]'>
  <mark class='Circle' />
  <encodings>
    <color column='[ds].[none:State:nk]' />
    <text column='[ds].[usr:This Week Value:qk]' />
  </encodings>
  <style>
    <style-rule element='cell'>
      <format attr='text-orientation' value='0' />
      <format attr='text-align' value='left' />
      <format attr='vertical-align' value='top' />
    </style-rule>
    <style-rule element='mark'>
      <format attr='size' value='1.4' />
      <format attr='mark-labels-show' value='true' />
    </style-rule>
  </style>
</pane>
```

### 最新期の手前で止まる平均線

列に「今週か」の判定を置いて今週を別ペインにしても、ペインごとの平均線は今週のペインに今週の値で 1 本引かれる。今週だけ NULL を返すアドホック計算を詳細に置き、平均線の `value-column` にすると、今週のペインは値が無く線が出ない。データソースの計算フィールドは増えない。

```xml
<!-- worksheet の datasource-dependencies -->
<column caption='Previous Weeks Value' datatype='real' name='[Calculation_901]' role='measure' type='quantitative'>
  <calculation class='tableau' formula='SUM(IF NOT [Is This Week] THEN [Value] END)' />
</column>
<column-instance column='[Calculation_901]' derivation='User' name='[usr:Calculation_901:qk]' pivot='key' type='quantitative' />

<!-- ペイン -->
<lod column='[ds].[usr:Calculation_901:qk]' />
<reference-line axis-column='[ds].[sum:Value:qk]' value-column='[ds].[usr:Calculation_901:qk]' formula='average'
    id='refline0' label-type='none' scope='per-pane' enable-instant-analytics='false' z-order='2' />
```

線を今週の位置まで延ばしたいなら、平均の定数フィールドを詳細に置き `formula='min'`・`scope='per-table'` にする（twb-pitfalls.md の定数フィールドの線）。

### マークの枠線

ペインの `element='mark'` に書く。線の太さは指定できず、細い線で固定。隣り合うタイルはそれぞれ枠を描くので、境目は 2 本分の幅になる。

```xml
<style-rule element='mark'>
  <format attr='has-stroke' value='true' />
  <format attr='stroke-color' value='#ffffff' />  <!-- タイルの境目は白。強調点は線と同じ色 -->
</style-rule>
```

### ラベルの表示条件

ペインの `element='mark'` に書く。`mark-labels-mode` の値は `all` / `most-recent` / `line-ends` / `range`（最小/最大）/ `selection` / `highlight`。

```xml
<style-rule element='mark'>
  <format attr='mark-labels-show' value='true' />
  <format attr='mark-labels-mode' value='line-ends' />
  <format attr='mark-labels-line-first' value='false' />  <!-- 始点には付けない -->
  <format attr='mark-labels-line-last' value='true' />
</style-rule>
```

線端に色のディメンションをラベルとして置けば、凡例の代わりになる。終点が近い線どうしは名前が重なる。

### Bar in Bar と、片側をラベル専用にする二重軸

二重軸の書き方は twb-pitfalls.md の「マークとシェルフ」に従う。ペインごとに `mark-color` と `size` を変える。

```xml
<cols>([ds].[usr:Target:qk] + [ds].[sum:Value:qk])</cols>
<pane id='1' x-axis-name='[ds].[usr:Target:qk]'>  <!-- 後ろの太い棒 -->
  <mark class='Bar' /><mark-sizing mark-sizing-setting='marks-scaling-off' />
  <style><style-rule element='mark'><format attr='mark-color' value='#d6d3c9' /><format attr='size' value='2.4' /></style-rule></style>
</pane>
<pane id='2' x-axis-name='[ds].[sum:Value:qk]'>   <!-- 前の細い棒 -->
  <mark class='Bar' /><mark-sizing mark-sizing-setting='marks-scaling-off' />
  <style><style-rule element='mark'><format attr='mark-color' value='#55575e' /><format attr='size' value='0.8' /></style-rule></style>
</pane>
```

合計だけをラベルにするときは、2 本目の軸に同じ値の別名の計算（例：アドホック計算 `SUM([Value])`）を置く。そのペインは色を外し、`<format attr='mark-transparency' value='0' />` とラベルを付ける。不透明度は 0（透明）〜255（不透明）。

### 発散型パレットの中心

ワークシートの `<style>` の `element='mark'` に書く。

```xml
<style-rule element='mark'>
  <encoding attr='color' center='0.0' field='[ds].[sum:Profit:qk]' palette='orange_blue_diverging_10_0' type='interpolated' />
</style-rule>
```

`num-steps='N'` で段階色、`reverse='true'` で反転。独自の色は `type='custom-interpolated'` にして `<color-palette type='ordered-diverging'>` を子に置く（この形は未実証）。

### タイトル内の色付き文字

`<layout-options>` を `<worksheet>` の最初の子に置く。

```xml
<worksheet name='...'>
  <layout-options><title><formatted-text>
    <run fontcolor='#1d1f24' fontsize='14'>Sales by month: </run>
    <run bold='true' fontcolor='#4e79a7' fontsize='14'>Furniture</run>
    ...
  </formatted-text></title></layout-options>
  <table>...
```

### 参照線のトリック（見えない余白・棒の内側の値・箇条グラフ）

`<reference-line>` はペインの中に置く。書式はワークシートの `<style>` に `id` 付きで書く。

```xml
<!-- 最大値の 110% に見えない線を置き、上端に余白を作る（軸の範囲がこの線で決まる） -->
<reference-line axis-column='[ds].[sum:Value:qk]' value-column='[ds].[sum:Value:qk]' formula='max'
    percentage-bands='true' symmetric='false' id='refline0' label-type='none' scope='per-pane'
    enable-instant-analytics='false' fill-above='false' fill-below='false' z-order='1'>
  <reference-line-value percentage='110' />
</reference-line>
<!-- style: <style-rule element='refband'><format attr='line-visibility' id='refline0' value='off' /> -->

<!-- 棒の内側先端に値（軸は伸びない）：セルごとの合計に線を引き、線を消してラベルだけ白で出す -->
<reference-line axis-column='[ds].[sum:Value:qk]' value-column='[ds].[sum:Value:qk]' formula='sum'
    id='refline0' label-type='value' scope='per-cell' enable-instant-analytics='false' z-order='1' />
<!-- style: <style-rule element='refline'> に、すべて id='refline0' で
     stroke-color #00000000 / line-visibility off / text-align left / vertical-align center /
     color #ffffff / font-weight bold -->

<!-- 箇条グラフ：詳細に置いた目標の 60% / 80% を帯、目標を線 -->
<reference-line axis-column='[ds].[sum:Value:qk]' value-column='[ds].[usr:Target:qk]' formula='average'
    percentage-bands='true' symmetric='false' fill-below='true' fill-above='false' id='refline1'
    label-type='none' scope='per-cell' enable-instant-analytics='false' z-order='1'>
  <reference-line-value percentage='60' /><reference-line-value percentage='80' />
</reference-line>
<reference-line axis-column='[ds].[sum:Value:qk]' value-column='[ds].[usr:Target:qk]' formula='average'
    id='refline0' label-type='none' scope='per-cell' enable-instant-analytics='false' z-order='2' />
```

棒の内側の値は、短い棒では切れる。参照線のラベルには既定で灰色の背景が付く。

### 前年を薄い面、今年を線

行の二重軸で、前年のペインを `<mark class='Area' />` にし、`mark-transparency` を 50〜100 程度（255 が不透明）にする。今年のペインは線にする。

## 対象外にした技

計算や工程が多く、少ない手順で見た目を良くする範囲を超えるもの。

- 自作チャート：Sankey、radial、waffle、donut、waterfall、panel chart、funnel、radar
- データの水増し・パスを使う技
- 見た目のための工程が多いもの：ダークモード、伸縮する動的凡例、シートの切り替え、計算を 5 本使う KPI カード
- 境界上：ダンベルチャート（二重軸＋パスで作れるが工程が多い）

Top N やクイック表計算の前期比は、見た目ではなく分析の機能なのでここでは扱わない。
