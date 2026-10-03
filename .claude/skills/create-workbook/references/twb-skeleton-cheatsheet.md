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

パラメータを参照するシートは、`<view>` の `<datasources>` と `<datasource-dependencies datasource='Parameters'>` にも `Parameters` を書く。

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

```xml
<dashboard name='Main'>
  <style/>
  <size maxheight='800' maxwidth='1200' minheight='800' minwidth='1200'/>
  <zones>
    <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
      <zone h='50000' id='2' name='KPI Trend' w='100000' x='0' y='0'>
        <zone-style>
          <format attr='border-color' value='#000000'/>
        </zone-style>
      </zone>
      <zone h='50000' id='3' name='Custom Sheet' w='100000' x='0' y='50000'/>
    </zone>
  </zones>
  <devicelayouts/>
</dashboard>
```

**重要**:
- 座標系は **100000 = 100%**（ダッシュボード全体の幅・高さに対する比率を 10万分率で）
- `zone[type-v2='layout-basic']` がコンテナ、子の `zone` が個別シート枠

## ウィンドウ（必須）

各シート・ダッシュボードに対応する `<window>` を `<windows>` 配下に追加する。

```xml
<windows source-height='800'>
  <window class='worksheet' name='KPI Trend'>
    <cards>...</cards>
  </window>
  <window class='dashboard' name='Main' maximized='true'>
    <cards>...</cards>
  </window>
</windows>
```

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
