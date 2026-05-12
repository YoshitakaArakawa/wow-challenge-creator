# Discussion — TC26 Challenge (2026-05-06)

## 重複チェック（直近3年・158問取得）

### 直近6ヶ月で「使い切られた」要素（避ける）
- KPI関連: KPI Trend Monitor (2026 W5)、KPI cards w/ Viz Ext (2026 W3)、Fake Viz in Tooltip (2026 W2)
- 期間比較・YoY: Baseline YoY Revenue (2026 W10)、Dynamic moving average (2026 W4)、Nulls in averages (2026 W6)
- DZV / コンテナ: Layout containers (2026 W11)、DZV+Filter Actions (2026 W8)
- Viz Extensions: Gauge/Radial (2026 W12)、KPI cards (2026 W3)
- Table Calc / LOD: Exploring Table Calcs vs LODs (2026 W7)
- Bar Chart Race: 2025 W47 / W48

### 過去3年で頻出のチャート種類（避ける）
Sankey, Marimekko, Bar Chart Race, Population Pyramid, Satellite, Trellis, Donut/Gauge, Comet, Funnel, Stem & Leaf, Tube Map, Drunken Tree, UpSet Plot, Scatterbox, Jitter系, Marginal Histogram, Control Chart, Parallel Coordinates, Candle, L-Shaped Bar, Christmas Tree, Waterfall

### TC関連の前例
- 2023 W19: jitterfly chart — TC23 Live Edition
- 2024 W17: TC23参加者の歩数データ
- 2024 W46: DataFam Europe Live
- 2025 W15 / 2026 W13: Community Month
→ TC連動の "Live Edition" 路線は前例あり

## ヒアリング結果

| 項目 | 決定 |
|---|---|
| 公開日 | 2026-05-06（TC26会期中） |
| 難易度 | 中級くらい、30分で解ける軽さ |
| Bonus | 上級者向けに別途用意する想定 |
| 方向性 | TC26 Live Edition 路線、AI/Agentセッションの偏りをVizにする |

## テーマ確定

**「AI Wave at TC26」**
TC26のセッション情報（手元のJSON）を題材に、AI/Agent系セッションがいかに多いかを可視化する。

### 元データ
- ファイル: `sessions.json` → `sessions.csv` に変換（364行、Vizziesイベント1件は時刻情報なしのため除外）
- 期間: 2026-05-05 〜 2026-05-07（3日間）
- 主要列: title, date, start_time, end_time, track, topic, level, session_type, room, description

### Viz要件（メイン）
- **レイアウト**: 横軸=日付（5/5・5/6・5/7）、縦軸=連続時間
- **マーク**: 円（1セッション=1円）
- **重なり処理**: ジッター（横方向に散らす）
- **色**: AI関連=目立つ色、その他=グレー
- **AIラベリング（2版用意）**:
  - **REGEXP版**: `REGEXP_MATCH([Title], '\bAI\b|Agent|Artificial')` — 1行で済む
  - **CONTAINS版**（正規表現に慣れていない参加者向け）:
    ```
    CONTAINS([Title], 'AI')
    OR CONTAINS(PROPER([Title]), 'Agent')
    OR CONTAINS(PROPER([Title]), 'Artificial')
    ```
    - **ポイント**: `CONTAINS([Title], 'AI')` は **case-sensitive** なので大文字 "AI" だけ拾い、"Main"/"Training"/"Wait" の小文字 "ai" は自然に除外される
    - Agent / Artificial は PROPER で大小文字を正規化 → 表記ゆれに強い
    - **注意**: 将来データに `RETAIL`, `FAIL`, `MAIN` 等の全大文字語が入ると False Positive になる可能性あり（現データはゼロ件確認済み）
  - 両版とも結果: 114 / 364 sessions（31.3%）
  - **会場での紹介フロー**: ①Naive `CONTAINS(LOWER([Title]), 'ai')` で "Main"/"Training"/"Wait" の誤マッチを体感 → ②case-sensitive + PROPER の CONTAINS版で解決 → ③REGEXP_MATCH でスマート解
- **BAN**: "114 / 364 sessions are AI-related (31%)"

### Bonus（仮）
Gantt化: 円ではなく開始〜終了の長さを線分やバーで描き、セッション時間の差を視覚化する。

### 次ステップ
1. プロトタイプ HTML を作成しレイアウト確認 → `prototype.html`
2. ユーザー確認後、Tableauで実装
3. 要件文を `requirements-ja.md` / `requirements-en.md` に作成

## 検討した代替案（不採用）

| 案 | 内容 | 不採用理由 |
|---|---|---|
| 案2: Topic Pulse | 時間帯別の積み上げ面チャート、AI/Non-AI色分け、データ密度化が必要 | 30分縛りに対しデータ密度化がやや重い |
| 案3: シンプルカレンダー | 案1の簡略版 | 学習価値が薄め |
| Bonus候補(b): 同時並行カウント | 各時刻のAI同時開催数を背景の薄い面で重ねる | Gantt化を優先 |
| Bonus候補(c): 詳細パネル連動 | クリックでセッション詳細表示 | Gantt化を優先 |
