# WOW Challenge Creator

Workout Wednesday (WOW) の Tableau 出題を作成するための支援環境。WOW は毎週水曜に公開されるスキルチャレンジで、参加者は提示されたビジュアライゼーションを再現する。

各工程の手順と詳細は、対応する Skill の SKILL.md にある。ここには工程のつながりだけを書く。セットアップは [README.md](README.md) を参照。

## 共通ルール

1. **直近3回と被らない** — 出題前に必ずWeb検索で確認
2. **難易度はユーザーが指定** — 問題作成時に確認する
3. **要件は英語＋日本語** — 両方の版を作る

## ユーザーに開いてもらうもの

ブラウザや Tableau Desktop での表示確認は、ユーザーが自分で開いて行う。Claude はブラウザやデスクトップを自動操作しない（Computer Use・Claude in Chrome・Playwright・組み込みブラウザを使わない）。Claude 自身の確認は、Cloud の描画（PNG・文字の表）、TWB の XML、ヘッドレス Chrome の撮影で行う。

開いてほしいものは、ユーザーがエクスプローラーで探さずに済む形でチャットに出す。

- ローカルのファイル（ドラフト HTML・`refine/compare.html`・`.twbx`）: 既定のアプリで開く 1 行コマンドを、単独のコードブロックで出す。パスはリポジトリ直下からの相対パスで書く（Windows は `start outputs/{theme}/refine/compare.html`、macOS は `open`）
- Cloud のワークブック: `refine/publish-result.json` の `webpageUrl` をそのまま出す
- 見てほしい点・してほしい操作を 1 行で添える

## 参照URL

| 情報 | URL |
|------|-----|
| WOW Tableau出題 | https://workout-wednesday.com/category/tableau/ |
| Tableau最新機能 | https://www.tableau.com/products/new-features |
| Tableau全リリース一覧 | https://www.tableau.com/products/all-features |
| Tableau公式ドキュメントスキーマ | https://github.com/tableau/tableau-document-schemas |

## 出題フォルダ

`outputs/YYYY-MM-DD-テーマ名/` に出題用フォルダを作る（英語ケバブケース、例: `outputs/2026-02-05-sankey-drilldown/`）。テーマ未定なら仮名で作成し、確定後にリネーム。すべての Skill はこのフォルダを共通ワークスペースとして読み書きし、ファイルで連携する。

テーマ直下には Markdown（`discussion.md`・`requirements-{ja,en}.md`）と `x-post.txt` だけを置く。重いファイルは次のサブフォルダに分ける（いずれも gitignore 済み）:

| サブフォルダ | 中身 |
|---|---|
| `prototype/` | ドラフト HTML |
| `refine/` | 作業用 `YYYYWNN.twbx`・展開した TWB・Cloud 描画・publish 結果 |
| `tmp/` | その他の中間生成物・スクリプト |
| `Archived/` | 出題ごとの非公開アセット |

## パイプライン

```
brainstorm
  ↓ discussion.md にテーマと選定理由
create-requirements（ドラフト）
  ↓ プロトタイプ HTML、作業用の要件、discussion.md に出題意図
create-workbook
  ↓ refine ループ: TWB 編集 → publish-to-cloud で Cloud に上書き・描画 → 比較
  ↓ ループ最終回の publish がそのまま公開版
create-requirements（確定）
  ↓ 完成した表示に合わせて、参加者向けの要件と Introduction を仕上げる
create-x-post
  ↓ x-post.txt
```

要件文は 2 回書く。ドラフトは `create-workbook` への仕様で、参加者に見せる版はワークブックの完成後に確定する。

### 分岐

| 条件 | 使う Skill |
|---|---|
| 既存Vizを参考にしたい (.twbx / Tableau Public) | `analyze-twbx`（要件ドラフトの前後） |
| 最新機能を確認したい | `search-tableau-features`（ブレスト中） |
| ユーザーが手動で .twbx を作った | `create-workbook` を飛ばし、`refine/` に置いて `publish-to-cloud` |
| 公開後にユーザーが Cloud 上で微修正した | `analyze-twbx`（Cloud経路）で pull → 差分を把握 → `create-workbook` で反映、または `publish-to-cloud --overwrite` |
