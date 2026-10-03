# WOW Challenge Creator

Workout Wednesday (WOW) Tableau出題を作成するための支援環境。

## Workout Wednesday とは

毎週水曜日に公開されるTableauスキルチャレンジ。参加者は提示されたビジュアライゼーションを可能な限り再現する。難易度は初級から上級まで幅広く、グローバルコミュニティで人気。

## 共通ルール

1. **直近3回と被らない** — 出題前に必ずWeb検索で確認
2. **難易度はユーザーが指定** — 問題作成時に確認する
3. **要件は英語＋日本語** — 英語で作成し、日本語も併記

## 参照URL

| 情報 | URL |
|------|-----|
| WOW Tableau出題 | https://workout-wednesday.com/category/tableau/ |
| Tableau最新機能 | https://www.tableau.com/products/new-features |
| Tableau全リリース一覧 | https://www.tableau.com/products/all-features |
| Tableau公式ドキュメントスキーマ | https://github.com/tableau/tableau-document-schemas |

## 出題フォルダ規約

`outputs/YYYY-MM-DD-テーマ名/` に出題用フォルダを作る（英語ケバブケース、例: `outputs/2026-02-05-sankey-drilldown/`）。テーマ未定なら仮名で作成し、確定後にリネーム。すべてのSkillはこのフォルダを共通ワークスペースとして読み書きする。

## ワークフロー — Skillパイプライン

WOW出題は次のパイプラインで作成する。各ステップは対応するSkillが担当し、Skill間は **出題フォルダのファイル** で連携する。

### 標準パイプライン

```
[1] brainstorm
      ↓ (discussion.md に記録、テーマ確定)
[2] create-requirements   ← 任意で prototype.html を併産
      ↓ (requirements-{ja,en}.md 確定)
[3] create-workbook
      ↓ (YYYYWNN.twbx 生成 → Cloud 描画ループで表示を詰める → Desktop で最終確認)
[4] publish-to-cloud
      ↓ (tmp/publish-result.json に Cloud URL。[3] のループ最終回がそのまま公開版)
[5] create-x-post
      ↓ (x-post.txt)
```

### 任意・分岐ステップ

| 条件 | 呼び出すSkill | タイミング |
|---|---|---|
| 既存Vizを参考にしたい (.twbx / Tableau Public) | `analyze-twbx` | [2] の前後 |
| 最新機能を確認したい | `search-tableau-features` | [1] のブレスト中 |
| Cloud上のWBをpull して現状確認したい (協働ループ) | `analyze-twbx` (Cloud経路) | [4] 以降のループ |
| ユーザーが手動でTWBX作成 | — | [3] スキップして配置 → [4] |
| 出題ごとの非公開アセット | — | `Archived/` に隔離（gitignore済み） |

### ワークブック命名と投稿先

- Cloud 上のワークブック名と `.twbx` ファイル名は `YYYYWNN`（例: `2026W40`）。タイトルは付けない
- 投稿先プロジェクトは `.env` の `TABLEAU_PROJECT_NAME`（既定 `99_WorkoutWednesday`）

### 描画ループ (Step 3 の内側)

Tableau Desktop は開いているワークブックを XML から再読込できない。表示の試行錯誤は Cloud を描画エンジンにして回す:

```
TWB 編集 → create-workbook iterate.ts (検証 → repack → publish --overwrite --render)
→ tmp/render/*.png を Claude が読む → 差分をフィードバック → TWB 編集 …
```

静止画で判断できない動作（ツールヒント・パラメータ・ハイライト）はブラウザで Cloud URL を開いて確かめる。画面操作はサブエージェントに委ねる。

### 協働ループ (Step 4以降)

publish後はユーザーがCloudで微修正することがある。次のループで反映する:

```
[publish-to-cloud] → ユーザーがCloud上で微修正 → [analyze-twbx Cloud経路でpull]
→ Claudeが差分把握 → [create-workbook 再生成] or 手直し指示 → [publish-to-cloud --overwrite]
```

### Skill間ファイル規約

| ファイル | 生成元 | 消費先 |
|---|---|---|
| `discussion.md` | brainstorm | create-requirements |
| `requirements-{ja,en}.md` | create-requirements | create-workbook, create-x-post |
| `prototype.html` | create-requirements (任意) | create-workbook (参考) |
| `tmp/workbook-patch.json` | create-workbook | (内部) |
| `tmp/cloud-pulled.twbx` | analyze-twbx (Cloud経路) | (Claude読み込み) |
| `*.twbx` | create-workbook | publish-to-cloud |
| `tmp/render/*.png` | publish-to-cloud (`--render`) | create-workbook (描画ループ、Claude 読み込み) |
| `tmp/publish-result.json` | publish-to-cloud | create-x-post |
| `backup/{wb}.twbx` | publish-to-cloud (overwrite時) | (ロールバック用) |
| `x-post.txt` | create-x-post | (最終成果物) |

### 初回セットアップ（依存）

各Skillスクリプトは初回のみ依存のインストールが必要。

```bash
# analyze-twbx
cd .claude/skills/analyze-twbx/scripts/twbx && npm install
cd ../tableau-public && npm install
cd ../cloud && npm install

# create-workbook
cd .claude/skills/create-workbook/scripts && npm install
# 初回XSDスナップショット取得 (任意、必要時)
npx tsx update-schemas.ts

# publish-to-cloud
cd .claude/skills/publish-to-cloud/scripts && pip install -r requirements.txt
```

`.env` はリポジトリ直下に置き（`.env.example` をコピーして使う）、`publish-to-cloud` と `analyze-twbx` の Cloud経路から参照される。Cloud 認証は OAuth のブラウザサインインで、初回は `python .claude/skills/publish-to-cloud/scripts/tableau_auth.py login` を実行してユーザーにサインインしてもらう。セッションは `.auth-cache/` に保存され両 Skill で共用される。
