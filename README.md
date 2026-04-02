# WOW Challenge Creator

[Claude Code](https://claude.ai/claude-code) を使って [Workout Wednesday](https://workout-wednesday.com/) の Tableau 出題を作成するためのツールキット。

## できること

1. **ブレスト** - アイデア発想と重複チェック
2. **プロトタイプ** - HTML + Chart.js でレイアウトを素早く視覚化
3. **要件作成** - 英語・日本語のバイリンガル要件文を一貫したスタイルで作成
4. **ワークブック解析** - .twbx から構造、計算フィールド、LOD式、依存関係を抽出
5. **スクリーンショット** - Tableau Public のビジュアライゼーションを PNG で取得
6. **Tableau 機能検索** - Tableau Desktop の最新機能を検索

## セットアップ

```bash
git clone https://github.com/YoshitakaArakawa/wow-challenge-creator.git
cd wow-challenge-creator
```

## 使い方

プロジェクトを Claude Code で開いて対話するだけで、以下のワークフローで出題を作成できる。

1. **出題フォルダの作成** - `outputs/YYYY-MM-DD-theme-name/` に要件文や議事録をまとめるフォルダを作成
2. **ブレスト** - 直近の出題との重複チェック、ヒアリング、アイデア展開。必要に応じて Tableau の最新機能も検索
3. **プロトタイプ（任意）** - Viz の方向性が固まったら HTML でレイアウトを素早く確認
4. **ワークブック作成** - 人間が Tableau Desktop で問題ワークブックを作成し、Tableau Public にパブリッシュする。TWBX と問題画像を出題フォルダに配置して連携する形でもOK
5. **要件作成** - テーマを正式な要件文に。Tableau Public の Viz をスクリーンショットやワークブック解析で分析し、要件に反映
6. **X 投稿文の作成** - 出題公開時の告知文を作成

## プロジェクト構成

```
.claude/skills/
  brainstorm/          # アイデア発想・重複チェック
  create-challenges/   # 要件作成 + twbx/スクリーンショットスクリプト
  tableau-features/    # Tableau Desktop 機能検索（キャッシュ付き）
outputs/               # 出題フォルダ（gitignore対象）
examples/              # 出題例（WOW2026 W12: https://www.workout-wednesday.com/2026w12tab/）
```

## 謝辞

`.claude/skills/create-challenges/scripts/` のワークブック解析スクリプトは [tableau-public-mcp](https://github.com/wjsutton/tableau-public-mcp)（[wjsutton](https://github.com/wjsutton) 作、[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)）を参考にしています。

## ライセンス

[MIT](LICENSE)
