---
name: create-workbook
description: 要件文を元にTableauワークブック(.twbx)を生成する。テンプレTWBXをベースに、計算フィールド・パラメータ・複数シート・ダッシュボード・デュアル軸を差分編集で組み立てる。「ワークブックを作って」「TWBXを生成」「Tableau Desktopで開ける状態で出して」で使用。Sankey等の特殊チャートは対象外。
---

# Tableauワークブック生成スキル

要件文（`requirements-en.md`）とプロトタイプ（任意 `prototype.html`）を入力に、`common/WOW Challenge Template.twbx` をベースに差分編集で `.twbx` を生成する。

## 設計の原則

**ハイブリッド戦略**（3層）:
1. **テンプレ流用**: `<workbook>` ルート、データソース、フォント等はテンプレ由来を温存
2. **レシピ挿入**: 計算フィールド、パラメータ、参照線、デュアル軸など定型は [references/chart-recipes/](references/chart-recipes/) のXMLテンプレを差し替え挿入
3. **局所スキーマ駆動**: 新規ワークシート全体は [references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md) と [references/schemas/](references/schemas/) を参照してXMLを書く

**ClaudeにTWB XMLを直書きさせず、パッチJSONを介する**。`apply-edits.ts` がパッチを決定論的にXMLに反映する。

## 標準手順

### Step 1: 前提確認
- `outputs/{theme}/requirements-en.md` を読む
- `outputs/{theme}/prototype.html` があれば参照（Vizイメージの認識合わせ）
- 出題で **Sample-Superstore以外のデータが必要か** を確認（Phase 2: `python/swap_datasource.py`）

### Step 2: スキーマ更新確認（任意）
新Tableau機能を試したい時など、最新XSDが必要そうなら:

```bash
npx tsx .claude/skills/create-workbook/scripts/check-schema-updates.ts
```

24時間キャッシュあり。更新があればリリースノートを表示し、ユーザー判断で `update-schemas.ts` 実行。

### Step 3: パッチJSONの起案
要件から次を抽出して `outputs/{theme}/tmp/workbook-patch.json` に書き出す（フォーマットは [パッチJSON仕様](#パッチJSON仕様) 参照）:
- 計算フィールド一覧
- パラメータ一覧
- シート構成（recipe名 or rawXml）
- ダッシュボード配置

書き出したらユーザーにレビューしてもらう。

### Step 4: 適用 → 検証 → 生成

```bash
SKILL=".claude/skills/create-workbook"
THEME_DIR="outputs/2026-MM-DD-theme"
PATCH="$THEME_DIR/tmp/workbook-patch.json"

# 1. テンプレTWBXを作業ディレクトリに展開
npx tsx $SKILL/scripts/unpack-template.ts --patch "$PATCH"

# 2. パッチをTWB XMLに適用
npx tsx $SKILL/scripts/apply-edits.ts --patch "$PATCH"

# 3. 検証 (XML well-formed + 必須要素 + フィールド参照整合性)
npx tsx $SKILL/scripts/validate-twb.ts --patch "$PATCH"

# 4. TWBX (ZIP) に再パッケージ
npx tsx $SKILL/scripts/repack-twbx.ts --patch "$PATCH"
```

Step 3で失敗したら、エラーメッセージを元にパッチJSONを修正し再実行（最大3回ループ）。

### Step 5: 目視確認 → パブリッシュへ

- 生成された `.twbx` をTableau Desktopで開いて確認
- 問題なければ `publish-to-cloud` Skillで Cloud へパブリッシュ

## パッチJSON仕様

```json
{
  "baseTemplate": "common/WOW Challenge Template.twbx",
  "outputPath": "outputs/{theme}/WOW2026 W{N}.twbx",
  "workingDir": "outputs/{theme}/tmp/wb-build",
  "dataSourceSwap": null,
  "parameters": [
    {
      "name": "Date Granularity",
      "datatype": "string",
      "domainType": "list",
      "values": ["Day", "Week", "Month"],
      "current": "Month"
    }
  ],
  "calculatedFields": [
    {
      "datasource": "federated.0abc",
      "caption": "Profit Ratio",
      "datatype": "real",
      "role": "measure",
      "type": "quantitative",
      "formula": "SUM([Profit])/SUM([Sales])"
    }
  ],
  "worksheets": [
    {
      "name": "KPI Trend",
      "recipe": "dual-axis",
      "params": {
        "DATASOURCE_NAME": "federated.0abc",
        "FIELD_X": "[Order Date]",
        "FIELD_Y1": "[Sales]",
        "FIELD_Y2": "[Profit Ratio]",
        "COLOR_PRIMARY": "#1f77b4",
        "COLOR_SECONDARY": "#ff7f0e"
      }
    },
    {
      "name": "Custom Sheet",
      "rawXml": "<worksheet name='Custom Sheet'>...</worksheet>"
    }
  ],
  "dashboards": [
    {
      "name": "Main",
      "size": {"width": 1200, "height": 800},
      "sheets": ["KPI Trend", "Custom Sheet"]
    }
  ]
}
```

- `recipe` は `references/chart-recipes/{recipe}.xml` のファイル名から `.xml` を除いたもの
- `recipe`/`rawXml` どちらか一方を指定（両方なら `rawXml` 優先）
- `dataSourceSwap` は Phase 2 で使用、Phase 1 は `null` 固定
- `workingDir` を省略すると `outputPath` のディレクトリ + `tmp/wb-build` を自動使用

## 参照ファイル

- [references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md) — TWB XML骨格チートシート
- [references/calc-field-patterns.md](references/calc-field-patterns.md) — 計算フィールド/LOD/パラメータの実例XML
- [references/chart-recipes/](references/chart-recipes/) — チャート種別ごとのレシピXML（プレースホルダ `{{NAME}}` 形式）
- [references/schemas/](references/schemas/) — Tableau公式XSDスナップショット（参照用）

## 初回セットアップ

```bash
cd .claude/skills/create-workbook/scripts && npm install
```

## 制約・対象外

- **対象外**: Sankey, Radial, Hex Tile, Map, Web Data Connector
- **Phase 1 制約**: Sample-Superstore固定、データソース置換なし、rawXml未対応、レシピは `bar-chart` / `line-chart` / `dual-axis` の3つのみ
- Tableau Desktop自動検証CLIは存在しない（最終確認は手動）
