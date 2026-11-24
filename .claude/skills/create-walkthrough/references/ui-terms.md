---
purpose: 手順書の英語版で使う Tableau の UI 語と、手順書の部品の見出しの対訳
note: 日本語版で書いた語を英語版でどう書くかの表。UI 語は Tableau Desktop 英語版の表記に揃える。フィールド名・シート名・シェルフ名（Columns・Rows・Color など）は日本語版でも英語のまま書くので、ここには載せない。表にない UI 語が出たら、英語版の Tableau の表記を確かめて足す
---

# UI 語の対訳

## 目次
- Tableau の操作とダイアログ
- マークと軸
- 並べ替えとフィルター
- 手順書の部品の見出し
- 書き方の約束

## Tableau の操作とダイアログ

| 日本語版 | 英語版 |
|---|---|
| 計算フィールドの作成... | Create Calculated Field... |
| 複製 | Duplicate |
| 表計算の編集... | Edit Table Calculation... |
| 入れ子になった計算 | Nested Calculations |
| 次を使用して計算 | Compute Using |
| 特定のディメンション | Specific Dimensions |
| 表（下） | Table (down) |
| 表（横） | Table (across) |
| 表（横、下） | Table (across then down) |
| セル | Cell |
| 再開間隔 | Restarting every |
| 右クリック | Right-click |
| ドラッグして〜に置く | Drag ... to ... |
| 新しいワークシート | New Worksheet |
| 新しいダッシュボード | New Dashboard |
| 空白（ダッシュボードのオブジェクト） | Blank |
| メジャーネーム / メジャーバリュー | Measure Names / Measure Values |
| リレーションシップ | Relationship |
| リレーションシップの計算 | Relationship calculation |
| ラベルの編集... | Edit Label... |
| 垂直方向のコンテナー / 水平方向のコンテナー | Vertical container / Horizontal container |
| 固定（ダッシュボードのサイズ） | Fixed size |

## マークと軸

| 日本語版 | 英語版 |
|---|---|
| マーク（カード） | Marks (card) |
| 多角形 | Polygon |
| 棒 | Bar |
| ガントバー | Gantt Bar |
| テキスト | Text |
| 色 / サイズ / ラベル / 詳細 / ツールヒント / パス | Color / Size / Label / Detail / Tooltip / Path |
| 不透明度 | Opacity |
| 軸の編集... | Edit Axis... |
| 固定（軸の範囲） | Fixed |
| 反転 | Reversed |
| ヘッダーの表示 | Show Header |
| 連続 / 不連続 | Continuous / Discrete |
| 集計 | Aggregate |
| 表計算（ピルの △） | Table calculation |

## 並べ替えとフィルター

| 日本語版 | 英語版 |
|---|---|
| 並べ替え... | Sort... |
| 手動 | Manual |
| フィールド（並べ替えの基準） | Field |
| 昇順 / 降順 | Ascending / Descending |
| ワークシートに適用 | Apply to Worksheets |
| このデータソースを使用するすべてのワークシート | All Using This Data Source |
| すべて（フィルターの全選択） | (All) |
| フィルターを表示 | Show Filter |

## 手順書の部品の見出し

| 日本語版 | 英語版 |
|---|---|
| 全体 | OVERVIEW |
| 章 N | CHAPTER N |
| 終章 | FINAL CHAPTER |
| 第 1 部 / 第 2 部 | Part 1 / Part 2 |
| ゴールのシート | Target sheet |
| このシートのディメンション | Dimensions on this sheet |
| 部品の分解図 | Component tree |
| 手順 N | Step N |
| やること | To do |
| ヒント | Hint |
| 答え：〜 | Answer: ... |
| 確認：この値が出れば正解（フィルターなし） | Check: you are correct if you get these values (no filter) |
| 〜（完成形） | ... (finished) |
| 〜（手順を終えた画面） | ... (after the steps) |
| フィルターなしで描画したもの | Rendered with no filter |
| このシートが描く部分（オレンジの枠）。完成版のダッシュボードをフィルターなしで描画したもの | The part this sheet draws (orange frame), from the finished dashboard rendered with no filter |
| 作る / 前の章 / データ（分解図の凡例） | Build / Earlier chapter / Data |
| 行レベル / 集計 / 表計算 / 表計算を参照（計算のタグ） | Row level / Aggregate / Table calc / Uses a table calc |
| 置かない（ディメンションの表） | Not placed |
| 〜の中（計算の使われる場所） | Inside ... |
| ← これを作る | ← build this |
| 検算シート | check sheet |
| 新規シートなので、書式は自分で付けます。 | This is a new sheet, so you apply the formatting yourself. |

## 書き方の約束

- UI 語は二重引用符で囲む。例: Right-click the pill and select "Edit Table Calculation..."
- 手順の動詞は命令形で書く（Create, Drag, Set, Check）
- 日本語版の「〜します」の説明文は、現在形の平叙文にする（The band narrows to a point.）
- 範囲は "A to B" と書き、矢印の並び（A → B）はそのまま使う
- 数値の書式は日本語版と同じにする
