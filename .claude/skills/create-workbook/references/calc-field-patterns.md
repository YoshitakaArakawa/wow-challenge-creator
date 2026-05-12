# 計算フィールド / LOD / パラメータ パターン集

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

## カラー条件分岐

### 閾値超過のフラグ
```
IF SUM([Profit Ratio]) >= 0.15 THEN 'High'
ELSEIF SUM([Profit Ratio]) >= 0.05 THEN 'Mid'
ELSE 'Low'
END
```

## TWB XMLエスケープのリマインド

formula の中で次を使う場合は XML エンティティでエスケープ:

| Tableau式 | XML埋め込み時 |
|---|---|
| `'Day'` | `&apos;Day&apos;` |
| `"hello"` | `&quot;hello&quot;` |
| `IF a < b` | `IF a &lt; b` |
| `a > b` | `a &gt; b` |
| `a & b` | `a &amp; b` |

apply-edits.ts が自動エスケープするが、`rawXml` モードで直書きする時は手動エスケープが必要。
