# Discussion: Viz Extensions Dashboard

## 日付
2026-03-23

## 重複チェック
Web検索で直近の出題を確認済み:
- Week 11: Can you use layout containers?（レイアウトコンテナ、角丸）
- Week 10: Baseline YoY Revenue（YoYチャート）
- Week 9: Can you build a parallel coordinates chart?（パラレルコーディネーツ）

→ Viz Extensionsをテーマにした出題はWOW2026で未出題。Viz Extensions自体がWOWで出題された実績もほぼなし。

## ヒアリング

### コンセプト
- **テーマ**: Tableau公式 Viz Extensions を活用したダッシュボード
- **難易度**: 中級 (Intermediate)
- **データ**: Sample Superstore
- **使用するViz Extensions**: Sankey, Radial, Tableau Table（すべてby Tableau）

### 背景
- Tableau 2024.2でViz Extensionsが一般提供開始、Tableau Exchangeで30+種類が利用可能
- 2025.3でSankeyとTableに機能強化（ラベル改善、カラーマッピング、フィルター改善等）
- Tableau Public でも Trusted Extensions が利用可能に
- Tableau以外のプロバイダー（LaDataViz, Infotopics, Actinvision, DataMa）も参入
- WOWではまだViz Extensionsを正面からテーマにした出題がない → 初出題として価値あり

### ユーザーの方向性
- 当初は2026.1新機能にフォーカスしたかったが、ドーナツ/サンバーストは2025.3の機能と判明
- Extensionsにフォーカスを転換、Tableau公式の3つのExtensionを組み合わせる方向に
- データはSample Superstore、ストーリーは特にこだわらない

## 議論の経緯

### バージョン確認
- ドーナツ＆サンバーストチャート → 2025.3で追加（2026.1ではない）
- カスタムカラーパレット → 2025.3で追加
- AIカラーパレット生成 → 2026.1で追加
- 角丸（Rounded Corners）→ 2026.1で追加（W11で出題済み）
- Mixed Geometries → 2026.1で追加

### Extension選定
- Tableau公式（by Tableau）のExtensionに絞る
- **Sankey**: カテゴリ間のフローを可視化。2025.3でラベル＆カラーマッピング改善
- **Radial**: Part-to-Wholeの円形表示。構成比を直感的に表現
- **Tableau Table**: インタラクティブなテーブル。フィルター改善、Null表示カスタマイズ（2025.3）

### Tableau Publicで使えるViz Extensions（判明分）
Sankey, Radial, Sunburst, Donut, Waterfall, Table, Network Diagram, Line Chart, Globe Path, Radar, DashPets 等 30+種類

プロバイダー: Tableau, LaDataViz, AppsForTableau (Infotopics), Actinvision, DataMa

## 決定事項
- テーマ名: **Viz Extensions Dashboard**
- Week 13（2026-03-25公開）
- 3つのViz Extensions（Sankey, Radial, Tableau Table）を使ったダッシュボード
- 次のステップ: プロトタイプ or 要件文の作成
