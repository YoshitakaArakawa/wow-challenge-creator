---
purpose: create-workbook のパッチ JSON に書く計算式の型集（LOD・表計算・日付・パラメータ・XML エスケープ）
fetched_at: 2026-10-01
source_last_known_update: 不明
note: 式の書き方だけを扱う。XML の骨格は twb-skeleton-cheatsheet.md、Desktop で失敗する落とし穴は twb-pitfalls.md が担当する。
---

# 計算フィールド / LOD / パラメータ パターン集

## 目次
- 基本パターン
- LOD式（ネスト LOD、期間の平均・SD、行ごとの文字列の連結）
- テーブル計算
- 日付関数
- パラメータを使った動的切替（選べる週を絞る動的パラメータ）
- カラー条件分岐
- TWB XMLエスケープのリマインド

create-workbook の `calculatedFields` パッチに書く `formula` を組み立てる際の参考。

## 基本パターン

### 比率
```
SUM([Profit]) / SUM([Sales])
```

### 差分・前期比
```
SUM([Sales]) - LOOKUP(SUM([Sales]), -1)
```

### 年累計 (YTD)
```
RUNNING_SUM(SUM([Sales]))
```

## LOD式

### FIXED — グループキーを固定
```
{ FIXED [Customer ID] : SUM([Sales]) }
{ FIXED [Region], [Category] : MAX([Order Date]) }
```

### INCLUDE — ビューより細かい粒度を含める
```
{ INCLUDE [Sub-Category] : AVG([Profit Ratio]) }
```

### EXCLUDE — ビューから次元を除外
```
{ EXCLUDE [Order Date] : SUM([Sales]) }
```

### ネストLOD
```
{ FIXED [Region] : AVG({ FIXED [Customer ID], [Region] : SUM([Sales]) }) }
```

外側の集計は内側 LOD の粒度（顧客ごと1行）で走り、行数で重み付けされない。ビューに `AVG({FIXED [Customer ID] : SUM([Sales])})` を直接置いたときの行重み付けとは違う。

### 期間の平均・標本SD（どのシートでも同じ値）
```
// 直前13週の週合計の平均。窓外の週は NULL になり集計から外れる
{ FIXED [Metric] : AVG({ FIXED [Metric], [Week] : SUM(IF [Weeks Ago] >= 1 AND [Weeks Ago] <= 13 THEN [Value] END) }) }
{ FIXED [Metric] : STDEV({ FIXED [Metric], [Week] : SUM(IF [Weeks Ago] >= 1 AND [Weeks Ago] <= 13 THEN [Value] END) }) }
```

窓の条件は内側に置く。外側に置くと行レベルの条件が混ざり、集計が行単位に落ちる。

### 行ごとの文字列を1つのマークに集める
```
{ FIXED : MAX(IF [Metric] = 'Sales' THEN [Phrase] END) } + { FIXED : MAX(IF [Metric] = 'Profit' THEN [Phrase] END) }
```

ディメンションをビューに置かずに、メンバーごとの値を順番を決めて連結する。表計算（`PREVIOUS_VALUE`）と最終行フィルタが要らない。

## テーブル計算

### 移動平均（前2期・現在・後2期）
```
WINDOW_AVG(SUM([Sales]), -2, 2)
```

### ランク
```
RANK(SUM([Sales]))
```

### パーセンタイル
```
PERCENTILE(SUM([Sales]), 0.75)
```

### 1個前の値
```
LOOKUP(SUM([Sales]), -1)
```

## 日付関数

### 期間指定
```
DATEADD('month', -3, [Order Date])
DATEDIFF('day', [Order Date], TODAY())
```

### 切り上げ・切り捨て
```
DATETRUNC('month', [Order Date])     // 月初に丸める
DATEPART('weekday', [Order Date])    // 曜日番号
```

### 動的な期間フィルタ
```
[Order Date] >= DATEADD('day', -14, TODAY())
```

## パラメータを使った動的切替

### 集計切替
```
CASE [Granularity]
  WHEN 'Day'   THEN DATETRUNC('day',   [Order Date])
  WHEN 'Week'  THEN DATETRUNC('week',  [Order Date])
  WHEN 'Month' THEN DATETRUNC('month', [Order Date])
END
```

### Top N フィルタ
```
RANK(SUM([Sales])) <= [Top N]
```

### 選べる週を絞る（動的パラメータの値の元）
週を選ばせるときは、日付の範囲ではなく週の始まりのリストにする（週の途中の日付を選べると利用者が迷う）。動的パラメータ（ブックを開いたときにフィールドから値を取る）の元にする計算で、対象外の週を NULL にすれば候補を絞れる。NULL は選択肢に出ない。
```
// Parameter list: the 8 week starts up to the default week
IF [Week] >= DATEADD('week', -7, #2026-08-09#) AND [Week] <= #2026-08-09#
THEN [Week] END
```
XML では、パラメータの `<column>` に `param-domain-type='list'` と `source-field='[データソース名].[計算の内部名]'` を書き、`<members>` は置かない（Desktop 2026.2 が保存した形）。

## カラー条件分岐

### 閾値超過のフラグ
```
IF SUM([Profit Ratio]) >= 0.15 THEN 'High'
ELSEIF SUM([Profit Ratio]) >= 0.05 THEN 'Mid'
ELSE 'Low'
END
```

## TWB XMLエスケープのリマインド

パッチ JSON の `formula` は apply-edits.ts が自動エスケープする。`rawXml` で直書きするときだけ手動でエスケープする。対応表は [twb-skeleton-cheatsheet.md](twb-skeleton-cheatsheet.md) の「XMLエンティティエスケープ」。
