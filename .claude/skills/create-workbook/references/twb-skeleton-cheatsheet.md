---
purpose: TWB (.twb) XML の骨格と、計算フィールド・パラメータ・ワークシート・ダッシュボード・ウィンドウの最小の書き方
fetched_at: 2026-05-12
source_last_known_update: 不明
note: TWB を直接編集してシートやダッシュボードを書くときの骨格だけを扱う。式の書き方は calc-field-patterns.md、Desktop で失敗する落とし穴は twb-pitfalls.md が担当する。例の属性値はテンプレ（source-build 2025.1.2、version 18.1）に合わせている。
---

# TWB XML骨格チートシート

## 目次
- ルート構造
- 計算フィールド (`<column>`)
- パラメータ
- ワークシート
- ダッシュボード
- ウィンドウ（必須）
- XMLエンティティエスケープ

## ルート構造

```xml
<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version='18.1' source-build='2025.1.2 (...)' source-platform='win' version='18.1' xmlns:user='...'>
  <document-format-change-manifest>...</document-format-change-manifest>
  <preferences>...</preferences>
  <datasources>
    <datasource name='Parameters' ...>...</datasource>
    <datasource caption='Orders (Sample - Superstore)' name='federated.xxxxx' ...>...</datasource>
  </datasources>
  <worksheets>
    <worksheet name='Sheet 1'>...</worksheet>
  </worksheets>
  <dashboards>
    <dashboard name='Main'>...</dashboard>
  </dashboards>
  <windows source-height='800'>...</windows>
</workbook>
```

**重要**:
- `<workbook>` の属性はテンプレのまま変えない。新しい属性を使えるかは `source-build` で決まる（twb-pitfalls.md の「Desktop に拒否される属性」）
- データソース名 `federated.xxxxx` の `xxxxx` は `apply-edits.ts` の出力（`primaryDatasource.name`）で確認する。`apply-edits.ts` は `Parameters` 以外で最初のデータソースを主データソースとして扱う
- パラメータは独立した `<datasource name='Parameters'>` 配下に置く（通常のデータソースとは別）。現行テンプレにはこのデータソースが無い
- テンプレには `<worksheet name='Sheet 1'>` と `<dashboard name='Goal'>`、それぞれの `<window>` が入っている。解答ワークブックでは削除する

## 計算フィールド (`<column>`)

データソース要素 `<datasource>` の直下に `<column>` を追加する。

### 基本形（測定値）
```xml
<column caption='Profit Ratio' datatype='real' default-format='p0%' name='[Calculation_001]' role='measure' type='quantitative'>
  <calculation class='tableau' formula='SUM([Profit])/SUM([Sales])'/>
</column>
```

### 基本形（ディメンション）
```xml
<column caption='Quarter Label' datatype='string' name='[Calculation_002]' role='dimension' type='nominal'>
  <calculation class='tableau' formula='&apos;Q&apos; + STR(DATEPART(&apos;quarter&apos;, [Order Date]))'/>
</column>
```

### LOD式（FIXED）
```xml
<column caption='Customer LTV' datatype='real' name='[Calculation_003]' role='measure' type='quantitative'>
  <calculation class='tableau' formula='{FIXED [Customer ID] : SUM([Sales])}'/>
</column>
```

### 重要な属性
- `name`: 内部ID。`[Calculation_NNN]` の形式が標準。apply-edits.ts は `001` からパッチの並び順に振る（既存の ID との衝突は確かめない。現行テンプレに計算フィールドは無い）。式の中や `<column-instance>` から計算フィールドを指すときは、キャプションではなくこの内部名を使う
- `caption`: 表示名（ユーザー可視）
- `datatype`: `integer` / `real` / `string` / `boolean` / `date` / `datetime`
- `role`: `measure` / `dimension`
- `type`: `quantitative` / `ordinal` / `nominal`
- `formula`: Tableau式。XMLエンティティエスケープ（`&apos;` `&quot;` `&amp;` `&lt;` `&gt;`）が必要

## パラメータ

`<datasource name='Parameters'>` 配下に `<column>` を追加。内部名は `[Parameter 1]` から連番にし、式やゾーンからは `[Parameters].[Parameter 1]` で指す。

現行テンプレには `Parameters` データソースが無いので、`<datasources>` の最初の子として足す:

```xml
<datasources>
  <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>
    <aliases enabled='yes' />
    <column caption='Select a Week' datatype='date' name='[Parameter 1]' param-domain-type='list' role='measure' type='quantitative' value='#2026-08-09#'>
      <calculation class='tableau' formula='#2026-08-09#' />
    </column>
  </datasource>
  <datasource caption='Orders (Sample - Superstore)' name='federated.xxxxx' ...>
```

パラメータを参照するシートは、`<view>` の `<datasources>` と `<datasource-dependencies datasource='Parameters'>` にも `Parameters` を書く。`<view>` の `<datasources>` では主データソースを先、`Parameters` を後に書く。逆にすると、Cloud が全シートを "does not have a valid data source" で拒否する（XSD 検証は通る）。

```xml
<view>
  <datasources>
    <datasource caption='Orders (Sample - Superstore)' name='federated.xxxxx' />
    <datasource name='Parameters' />
  </datasources>
  <datasource-dependencies datasource='Parameters'>
    <column caption='Select a Week' datatype='date' name='[Parameter 1]' ...>...</column>
  </datasource-dependencies>
  <datasource-dependencies datasource='federated.xxxxx'>...</datasource-dependencies>
```

### リスト型パラメータ
```xml
<column caption='Date Granularity' datatype='string' name='[Parameter 1]' param-domain-type='list' role='measure' type='nominal' value='&quot;Month&quot;'>
  <members>
    <member alias='Day' value='&quot;Day&quot;'/>
    <member alias='Week' value='&quot;Week&quot;'/>
    <member alias='Month' value='&quot;Month&quot;'/>
  </members>
  <aliases>
    <alias key='&quot;Day&quot;' value='Day'/>
    <alias key='&quot;Week&quot;' value='Week'/>
    <alias key='&quot;Month&quot;' value='Month'/>
  </aliases>
</column>
```

### 範囲型パラメータ（整数）
```xml
<column caption='Top N' datatype='integer' name='[Parameter 2]' param-domain-type='range' role='measure' type='quantitative' value='10'>
  <range granularity='1' min='1' max='100'/>
</column>
```

## ワークシート

```xml
<worksheet name='KPI Trend'>
  <table>
    <view>
      <datasources>
        <datasource caption='Sample - Superstore' name='federated.xxxxx'/>
      </datasources>
      <datasource-dependencies datasource='federated.xxxxx'>
        <column-instance column='[Order Date]' derivation='Year' name='[yr:Order Date:ok]' pivot='key' type='ordinal'/>
        <!-- 参照する列ごとに column-instance を列挙 -->
      </datasource-dependencies>
      <aggregation value='true'/>
    </view>
    <rows>[federated.xxxxx].[sum:Sales:qk]</rows>
    <cols>[federated.xxxxx].[yr:Order Date:ok]</cols>
    <pane>
      <view>
        <breakdown value='auto'/>
      </view>
      <mark class='Line'/>
    </pane>
  </table>
</worksheet>
```

**重要**: `<rows>` / `<cols>` の値は `[datasourceName].[fieldName]` の形式。`fieldName` は集計済みフィールド名（`[sum:Sales:qk]` など）か単純なフィールド名。

### マーククラス一覧
`Automatic`, `Bar`, `Line`, `Pie`, `Square`, `Circle`, `Shape`, `Text`, `Map`, `Polygon`, `GanttBar`, `Histogram`, `Heatmap`

## ダッシュボード

固定サイズで、縦の流れコンテナに段を積む形。段の中で横に並べるときは、横の流れコンテナを入れ子にする。

```xml
<dashboard enable-sort-zone-taborder='true' name='Main'>
  <style />
  <size maxheight='1000' maxwidth='420' minheight='1000' minwidth='420' sizing-mode='fixed' />
  <zones>
    <zone id='100' param='vert' type-v2='layout-flow' x='0' y='0' w='100000' h='100000'>
      <!-- テキスト。改行は「Æ」と生の改行だけの run（閉じタグを次の行に書く） -->
      <zone id='101' type-v2='text' fixed-size='58' is-fixed='true' forceUpdate='true' x='2857' y='1149' w='94286' h='5556'>
        <formatted-text>
          <run bold='true' fontcolor='#6e6e6e' fontsize='8'>SUPERSTORE</run>
          <run>Æ
</run>
          <run bold='true' fontcolor='#1d1f24' fontsize='16'>Weekly Health Check</run>
        </formatted-text>
        <zone-style>
          <format attr='border-style' value='none' />
          <format attr='margin' value='4' />
        </zone-style>
      </zone>
      <!-- 余白 -->
      <zone id='102' type-v2='empty' fixed-size='12' is-fixed='true' x='2857' y='6705' w='94286' h='1149' />
      <!-- シート（高さ固定） -->
      <zone id='116' name='KPI' show-title='false' fixed-size='90' is-fixed='true' x='2857' y='42305' w='94286' h='8621' />
      <!-- 横に 2 枚、均等に並べる -->
      <zone id='119' type-v2='layout-flow' param='horz' layout-strategy-id='distribute-evenly' fixed-size='152' is-fixed='true' x='2857' y='50925' w='94286' h='12868'>
        <zone id='117' name='Sales Chart' show-title='false' x='2857' y='50925' w='47143' h='12868' />
        <zone id='118' name='Profit Chart' show-title='false' x='50000' y='50925' w='47143' h='12868' />
      </zone>
    </zone>
  </zones>
  <devicelayouts />
</dashboard>
```

**重要**:
- `x` / `y` / `w` / `h` は **100000 = 100%**（ダッシュボード全体に対する 10 万分率）。vendor の examples の JSON はピクセルで書かれているが、TWB では 10 万分率で書く
- 流れコンテナ（`type-v2='layout-flow'`）の中のゾーンは、`fixed-size`（ピクセル）と `is-fixed='true'` で大きさを決める。`x` / `y` / `w` / `h` も書く
- `param='vert'` が縦、`param='horz'` が横。`layout-strategy-id='distribute-evenly'` で子を均等に配分する
- `id` はダッシュボード内で重複させない
- シートのゾーンは `name` にシート名を書き、`type-v2` は付けない

## ウィンドウ（必須）

各シート・ダッシュボードに対応する `<window>` を `<windows>` 配下に追加する。

```xml
<windows source-height='800'>
  <window class='worksheet' name='KPI Trend'>
    <cards>...</cards>
  </window>
  <window class='dashboard' name='Main' maximized='true'>
    <viewpoints>
      <viewpoint name='KPI Trend'>
        <zoom type='entire-view' />
      </viewpoint>
    </viewpoints>
    <active id='-1' />
  </window>
</windows>
```

ダッシュボードの `<window>` には、載せたシートごとに `<viewpoint>` を書き、`<zoom type='entire-view' />`（Fit の「ビュー全体」）を指定する。無いとシートが標準サイズで描かれ、ゾーンにスクロールバーが出たり、テキストのシートが `#####` になったりする。

apply-edits.ts は `<cards/>` を空のまま挿入し、Tableau Desktopが初回オープン時に自動補完するのを期待する（★要検証）。

## XMLエンティティエスケープ

| 文字 | エスケープ |
|---|---|
| `'` (シングルクォート) | `&apos;` |
| `"` (ダブルクォート) | `&quot;` |
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |

formula 属性の中で計算式を書く時、Tableauの文字列リテラル `'foo'` はXML的に `&apos;foo&apos;` になる。パッチ JSON の `formula` は apply-edits.ts が自動エスケープするので、手動で変換するのは `rawXml` で直書きするときだけ。
