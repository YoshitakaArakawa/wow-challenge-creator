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
npx tsx .claude/skills/analyze-twbx/scripts/twbx/structure.ts "<mainTwbPath>" [--fields]

# 3. 詳細分析
npx tsx .claude/skills/analyze-twbx/scripts/twbx/calculated-fields.ts "<mainTwbPath>"
npx tsx .claude/skills/analyze-twbx/scripts/twbx/lod-expressions.ts "<mainTwbPath>"
npx tsx .claude/skills/analyze-twbx/scripts/twbx/dependencies.ts "<mainTwbPath>"
```

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
リポジトリ直下の `.env` に Tableau Cloud の PAT 認証情報が設定されていること（`.env.example` 参照）。

### 使い方

```bash
# サイト内のワークブック一覧 (名前検索したい時)
npx tsx .claude/skills/analyze-twbx/scripts/cloud/list-workbooks.ts [--project "WOW Challenges"]

# 名前またはIDで指定してダウンロード
npx tsx .claude/skills/analyze-twbx/scripts/cloud/download-from-cloud.ts \
  --name "WOW2026 W19" --output-dir "outputs/2026-MM-DD-theme-name"
# または
npx tsx .claude/skills/analyze-twbx/scripts/cloud/download-from-cloud.ts \
  --id <workbook-id> --output-dir "outputs/2026-MM-DD-theme-name"
```

ダウンロードした .twbx は `outputs/{theme}/tmp/cloud-pulled.twbx` に保存される。以降は経路1の手順で解析できる。

初回のみ `cd .claude/skills/analyze-twbx/scripts/cloud && npm install`。

## ツール一覧（参考）

| スクリプト | 用途 |
|---|---|
| `scripts/twbx/download.ts` | Tableau Public からTWBXダウンロード |
| `scripts/twbx/unpack.ts` | .twbx (ZIP) 展開 |
| `scripts/twbx/structure.ts` | データソース・シート・ダッシュボード一覧 |
| `scripts/twbx/calculated-fields.ts` | 計算フィールド抽出 |
| `scripts/twbx/dependencies.ts` | フィールド依存グラフ |
| `scripts/twbx/lod-expressions.ts` | FIXED/INCLUDE/EXCLUDE 抽出 |
| `scripts/tableau-public/screenshot.ts` | 静的画像API でPNG取得 |
| `scripts/cloud/list-workbooks.ts` | Cloud上のワークブック一覧 |
| `scripts/cloud/download-from-cloud.ts` | Cloudから .twbx 取得 |
