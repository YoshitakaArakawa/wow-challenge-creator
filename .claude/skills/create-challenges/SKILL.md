---
name: create-challenges
description: WOW出題の要件文作成とワークブック解析。「要件を書いて」「問題文を作って」「このVizを解析して」で使用。
---

# WOW要件作成＋解析スキル

## 手順

### 1. テーマ確認
ブレスト結果またはユーザー指定のテーマを確認する。
- テーマ、使用機能、難易度、データセットが決まっているか
- 未決定の場合はブレストスキルに誘導する

### 2. Vizの視覚確認＋解析
Tableau Public URLが分かる場合はスクリーンショットを取得してVizの見た目を確認する（後述「スクリーンショットツール」を参照）。
必要に応じてTWBX解析スクリプトで構造・計算フィールドを解析する（後述「TWBX解析ツール」を参照）。

### 3. 要件文の作成
`.claude/skills/create-challenges/wow-style-guide.md` を参照し、WOWの標準的なスタイルで要件文を作成する。

- まず日本語でユーザーと内容を詰める
- 確定後、英語版を作成する（直訳ではなく、WOWコミュニティのトーンに合わせる）
- スコープは **Introduction** と **Requirements** の2セクションのみ
- 英語版MDファイルの末尾に、HTMLコメントとしてサイト掲載用のHTML版を埋め込む（詳細はスタイルガイド参照）

作成後、ユーザーに提示してレビューを受ける。

### 4. 成果物の保存
出題フォルダに保存する:
- `outputs/YYYY-MM-DD-theme-name/requirements-ja.md` （日本語版）
- `outputs/YYYY-MM-DD-theme-name/requirements-en.md` （英語版 + HTML版を末尾にコメントで埋め込み）

---

## スクリーンショットツール

`.claude/skills/create-challenges/scripts/tableau-public/` にある。Tableau Publicの静的画像APIを利用してダッシュボードのPNGを取得する。

### 前提
```bash
cd scripts/tableau-public && npm install  # 初回のみ
```

### 使い方
```bash
npx tsx .claude/skills/create-challenges/scripts/tableau-public/screenshot.ts <tableauPublicUrl> [--output-dir <出題フォルダ>]
```
- Tableau PublicのURLをそのまま渡す
- `--output-dir` で出題フォルダを指定すると `{フォルダ}/tmp/screenshots/` に保存される
- 出力の `filePath` をRead toolで開くと画像を視覚的に確認できる

### 例
```bash
npx tsx .claude/skills/create-challenges/scripts/tableau-public/screenshot.ts "https://public.tableau.com/app/profile/yoshitaka6076/viz/WOW2026W5/WOW2026W4" --output-dir "outputs/2026-02-05-kpi-trigger-monitor"
```

---

## TWBX解析ツール

`.claude/skills/create-challenges/scripts/twbx/` に7つのCLIスクリプトがある。すべてJSON出力。

### 前提
```bash
cd scripts/twbx && npm install  # 初回のみ
```

### ツール一覧と使い方

#### 1. download - TWBXダウンロード
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/download.ts <workbookName> [--output-dir <出題フォルダ>]
```
- Tableau PublicからTWBXをダウンロード（allowDataAccessを事前検証）
- workbookNameはTableau PublicのURL末尾のパス部分

#### 2. unpack - TWBX展開
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/unpack.ts <twbxFilePath> [--output-dir <出題フォルダ>]
```
- .twbx（ZIP形式）を展開し、ファイル一覧を返す
- 出力の `mainTwbPath` を後続ツールで使用

#### 3. structure - ワークブック構造
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/structure.ts <twbFilePath> [--fields]
```
- データソース、ワークシート、ダッシュボード、パラメータの全体構造
- `--fields` でフィールド詳細を含める

#### 4. calculated-fields - 計算フィールド
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/calculated-fields.ts <twbFilePath> [--no-hidden] [--no-deps]
```
- 計算フィールド一覧（数式、型、依存先）
- パラメータ、ソースフィールドも抽出

#### 5. dependencies - 依存関係グラフ
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/dependencies.ts <twbFilePath> [--source-fields]
```
- 計算フィールド間の依存関係をツリー表示
- ルート/リーフ計算の特定、循環依存の検出

#### 6. lod-expressions - LOD式
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/lod-expressions.ts <twbFilePath> [--no-usage]
```
- FIXED/INCLUDE/EXCLUDE式の抽出・分類・説明生成
- ネストされたLODの検出

#### 7. data-profile - データプロファイル
```bash
npx tsx .claude/skills/create-challenges/scripts/twbx/data-profile.ts <extractionPath> [--no-images]
```
- CSV/Excel/JSONのカラム名抽出
- .hyper/.tdeは非対応（Tableau独自形式）

### 典型的な解析フロー
`--output-dir` を指定すると、中間成果物が出題フォルダの `tmp/` に格納される。
```bash
OUTPUT_DIR="outputs/2026-02-05-kpi-trigger-monitor"

# 1. スクリーンショット（Tableau Public URLが分かる場合）
npx tsx .claude/skills/create-challenges/scripts/tableau-public/screenshot.ts "<url>" --output-dir "$OUTPUT_DIR"

# 2. 展開（ローカルTWBX or ダウンロード済みTWBX）
npx tsx .claude/skills/create-challenges/scripts/twbx/unpack.ts "<twbxPath>" --output-dir "$OUTPUT_DIR"
# → mainTwbPath, extractionPath を取得

# 3. 構造確認（read-onlyなので --output-dir 不要）
npx tsx .claude/skills/create-challenges/scripts/twbx/structure.ts "<mainTwbPath>"

# 4. 必要に応じて詳細分析
npx tsx .claude/skills/create-challenges/scripts/twbx/calculated-fields.ts "<mainTwbPath>"
npx tsx .claude/skills/create-challenges/scripts/twbx/lod-expressions.ts "<mainTwbPath>"
npx tsx .claude/skills/create-challenges/scripts/twbx/data-profile.ts "<extractionPath>"
```
