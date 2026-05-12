# WOW Challenge Creator

[Claude Code](https://claude.ai/claude-code) を使って [Workout Wednesday](https://workout-wednesday.com/) の Tableau 出題を作成するためのツールキット。

## できること

1. **ブレスト** - アイデア発想と重複チェック
2. **要件作成** - 英語・日本語のバイリンガル要件文を一貫したスタイルで作成。任意で HTML + Chart.js プロトタイプを併産
3. **ワークブック解析** - .twbx から構造、計算フィールド、LOD式、依存関係を抽出。Tableau Public スクリーンショット取得、Tableau Cloud 上のワークブック取得にも対応
4. **ワークブック生成** - 要件からテンプレート差分編集で .twbx を生成（中間スコープ）
5. **Tableau Cloud パブリッシュ** - PAT 認証、上書き対応、上書き時バックアップ
6. **X 投稿文の作成** - 出題公開時の告知文を作成
7. **Tableau 機能検索** - Tableau Desktop の最新機能を検索

## セットアップ

```bash
git clone https://github.com/YoshitakaArakawa/wow-challenge-creator.git
cd wow-challenge-creator
cp .env.example .env   # Tableau Cloud 認証情報を埋める
```

## 使い方

プロジェクトを Claude Code で開いて対話するだけで、以下のワークフローで出題を作成できる。

1. **出題フォルダの作成** - `outputs/YYYY-MM-DD-theme-name/`
2. **ブレスト** (`brainstorm`) - 直近の出題との重複チェック、ヒアリング、アイデア展開
3. **要件作成** (`create-requirements`) - 英語+日本語の要件文。任意で HTML プロトタイプ
4. **ワークブック生成** (`create-workbook`) - テンプレ差分編集 + チャートレシピで .twbx を生成
5. **Cloud パブリッシュ** (`publish-to-cloud`) - Tableau Cloud にアップロード
6. **X 投稿文の作成** (`create-x-post`) - Cloud URL を含めた告知文

任意・分岐: `analyze-twbx`（既存Viz・Cloud上WB解析）、`tableau-features`（新機能検索）。詳細は [CLAUDE.md](CLAUDE.md) のワークフロー節を参照。

## プロジェクト構成

```
.claude/skills/
  brainstorm/          # アイデア発想・重複チェック
  analyze-twbx/        # TWBX解析 (ローカル / Tableau Public / Tableau Cloud)
  create-requirements/ # 要件文 + プロトタイプHTML
  create-workbook/     # .twbx 生成 (テンプレ差分 + チャートレシピ)
  publish-to-cloud/    # Tableau Cloud パブリッシュ
  create-x-post/       # X (Twitter) 投稿文
  tableau-features/    # Tableau Desktop 機能検索（キャッシュ付き）
common/                # 共通アセット (テンプレートTWBX、サンプルデータ)
outputs/               # 出題フォルダ（gitignore対象）
examples/              # 出題例（WOW2026 W12: https://www.workout-wednesday.com/2026w12tab/）
```

## 謝辞

`.claude/skills/analyze-twbx/scripts/twbx/` のワークブック解析スクリプトは [tableau-public-mcp](https://github.com/wjsutton/tableau-public-mcp)（[wjsutton](https://github.com/wjsutton) 作、[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)）を参考にしています。

## ライセンス

[MIT](LICENSE)
