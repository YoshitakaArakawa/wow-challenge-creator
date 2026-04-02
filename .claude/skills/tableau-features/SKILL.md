---
name: tableau-features
description: Tableau Desktopの新機能を検索・一覧表示。「最近の新機能は？」「Sankey関連の機能は？」「機能キャッシュ更新して」で使用。
user-invocable: true
argument-hint: [検索キーワード or "update"]
allowed-tools: WebFetch, Read, Write, Glob
---

# Tableau Desktop機能検索スキル

Tableauのメジャーリリースから **Desktop向け機能** を抽出し、キャッシュファイルに保存・検索する。

## キャッシュファイル

- **パス**: `.claude/skills/tableau-features/features-cache.md`
- **対象**: 過去1年間のメジャーリリースのみ
- **フォーマット**: 下記参照

## 手順

### 1. キャッシュの確認

`.claude/skills/tableau-features/features-cache.md` をGlobで確認する。

- **ファイルが存在する場合**: Readで読み込み、`Last updated` の日付を確認
  - ユーザーが「更新して」と明示した場合 → Step 2（強制更新）へ
  - それ以外 → Step 3（検索）へ
- **ファイルが存在しない場合**: Step 2（初回構築）へ

### 2. キャッシュの構築・更新

#### 2a. リリースURL一覧の取得
`https://www.tableau.com/products/all-features` をWebFetchし、メジャーリリースのURLを抽出する。

**メジャーリリースURLのパターン**:
- 最新: `https://www.tableau.com/products/new-features`
- 過去: `https://www.tableau.com/{year}-{quarter}-features`（例: `2025-3-features`）

月次リリース（`2025-2-november-features` 等）は**除外**する。

#### 2b. 過去1年間のフィルタ
取得したURLのうち、**現在日付から1年以内のリリース**のみを対象とする。
- 年とクォーターからおおよそのリリース時期を推定して判断する
- 例: 現在が2026年3月なら、2025.1（2025年初頭）以降が対象

#### 2c. 各リリースページからDesktop機能を抽出
対象の各URLをWebFetchし、以下の条件で機能を抽出する:
- **Product = Tableau Desktop** のセクションに記載されている機能
- **複数製品にまたがる機能**で Desktop が含まれるもの（例: "Desktop, Cloud, Public"）
- Server専用、Cloud専用、Prep専用、Next専用の機能は**除外**

各機能について以下を記録:
- **Feature**: 機能名（英語）
- **Description**: 簡潔な説明（英語、1行）

#### 2d. キャッシュファイルの書き込み
以下のフォーマットで `.claude/skills/tableau-features/features-cache.md` に保存する:

```markdown
<!-- Last updated: YYYY-MM-DD -->

## {Release Name} (URL)

| Feature | Description |
|---------|-------------|
| ... | ... |

## {Release Name} (URL)

| Feature | Description |
|---------|-------------|
| ... | ... |
```

- リリースは新しい順に並べる
- 過去1年より古いリリースが既存キャッシュにある場合は削除する

更新完了後、追加・削除されたリリースをユーザーに報告する。

### 3. 検索・表示

キャッシュファイルをReadで読み込み、ユーザーの質問に応じて回答する。

**引数・質問のパターン**:

| 入力例 | 動作 |
|--------|------|
| （引数なし）「最近の新機能は？」 | 全リリースの機能一覧を表示 |
| `Sankey` / 「Sankey関連は？」 | キーワードで機能をフィルタして表示 |
| `2025.3` / 「2025.3の機能は？」 | 指定リリースの機能のみ表示 |
| `update` / 「キャッシュ更新して」 | Step 2を実行（強制更新） |

検索結果は簡潔なテーブル形式で返す。該当がない場合はその旨を伝える。
