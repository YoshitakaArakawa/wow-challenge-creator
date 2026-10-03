---
name: analyze-twbx
description: Tableauワークブック(.twbx)の構造・計算フィールド・LOD・依存関係を解析する。ローカルファイル、Tableau Public URL、Tableau Cloud上のワークブックの3経路に対応。「このTWBXを解析して」「Public Vizを見せて」「Cloudの最新版を取得して構造を確認」で使用。
---

# TWBX解析スキル

ワークブックの構造・計算フィールド・LOD・依存関係をJSONで出力する。スクリーンショットも取得可能。

## 経路1: ローカル .twbx を解析

```bash
OUTPUT_DIR="outputs/2026-MM-DD-theme-name"

# 1. 展開
npx tsx .claude/skills/analyze-twbx/scripts/twbx/unpack.ts "<twbxPath>" --output-dir "$OUTPUT_DIR"
# → mainTwbPath, extractionPath が出力される

# 2. 構造確認
npx tsx .claude/skills/analyze-twbx/scripts/twbx/structure.ts "<mainTwbPath>" [--fields] [--usage]

# 3. 詳細分析
npx tsx .claude/skills/analyze-twbx/scripts/twbx/calculated-fields.ts "<mainTwbPath>"
npx tsx .claude/skills/analyze-twbx/scripts/twbx/lod-expressions.ts "<mainTwbPath>"
npx tsx .claude/skills/analyze-twbx/scripts/twbx/dependencies.ts "<mainTwbPath>"
```

`--usage` を付けると、次の 2 つが加わる。ワークブックの簡素化レビュー（create-workbook Step 5）に使う。

- `fieldUsage`：計算フィールド・パラメータ・シート内だけの計算ごとに、使われているシートと棚（`rows` / `cols` / `color` / `text` / `lod` / `filter` / `reference-line` / `label-text` / `tooltip-text` など）、参照する・参照されるフィールド、`unused`（どこからも使われない）
- `sheetsNotOnDashboard`：どのダッシュボードにも載っていないワークシート

初回のみ `cd .claude/skills/analyze-twbx/scripts/twbx && npm install`。

## 経路2: Tableau Public からダウンロード + スクリーンショット

```bash
OUTPUT_DIR="outputs/2026-MM-DD-theme-name"

# スクリーンショット (静的画像API)
npx tsx .claude/skills/analyze-twbx/scripts/tableau-public/screenshot.ts \
  "<tableauPublicUrl>" --output-dir "$OUTPUT_DIR"

# TWBXダウンロード (allowDataAccessを事前検証)
npx tsx .claude/skills/analyze-twbx/scripts/twbx/download.ts <workbookName> --output-dir "$OUTPUT_DIR"
```

スクリーンショットは `--output-dir` の `tmp/screenshots/` に保存。`filePath` をReadで開けば画像を視覚的に確認できる。

初回のみ `cd .claude/skills/analyze-twbx/scripts/tableau-public && npm install`。

## 経路3: Tableau Cloud から取得 (協働ループ)

publish後にCloud上で微修正されたワークブックを取得し、差分を解析する用途。

### 前提
リポジトリ直下の `.env` に `TABLEAU_SERVER_URL` / `TABLEAU_SITE_ID` があり、OAuth セッションがキャッシュされていること。セッションがない・失効したときは publish-to-cloud Skill の `tableau_auth.py login` でブラウザサインインしてもらう（`.auth-cache/session.json` を共用）。

### 使い方

```bash
# サイト内のワークブック一覧 (名前検索したい時)
npx tsx .claude/skills/analyze-twbx/scripts/cloud/list-workbooks.ts [--project "99_WorkoutWednesday"]

# 名前またはIDで指定してダウンロード
npx tsx .claude/skills/analyze-twbx/scripts/cloud/download-from-cloud.ts \
  --name "2026W40" --output-dir "outputs/2026-MM-DD-theme-name"
# または
npx tsx .claude/skills/analyze-twbx/scripts/cloud/download-from-cloud.ts \
  --id <workbook-id> --output-dir "outputs/2026-MM-DD-theme-name"
```

ダウンロードした .twbx は `outputs/{theme}/tmp/cloud-pulled.twbx` に保存される。以降は経路1の手順で解析できる。

初回のみ `cd .claude/skills/analyze-twbx/scripts/cloud && npm install`。
