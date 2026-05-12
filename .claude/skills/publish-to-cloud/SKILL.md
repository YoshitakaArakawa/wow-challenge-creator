---
name: publish-to-cloud
description: 生成済みの.twbxをTableau Cloudにパブリッシュする。PAT認証、上書き対応、上書き時の事前バックアップ、指数バックオフリトライ。「Cloudにパブリッシュして」「TWBXをアップロード」「ワークブックを公開」で使用。
---

# Tableau Cloud パブリッシュスキル

`create-workbook` で生成した、または手動で配置した `.twbx` を Tableau Cloud にアップロードする。

## 前提

リポジトリ直下の `.env` に Cloud 認証情報が設定されていること（[`.env.example`](../../../.env.example) 参照）:

```
TABLEAU_SERVER_URL=https://10ax.online.tableau.com
TABLEAU_SITE_ID=
TABLEAU_PAT_NAME=
TABLEAU_PAT_VALUE=
TABLEAU_PROJECT_NAME=WOW Challenges
```

初回のみ依存をインストール:

```bash
cd .claude/skills/publish-to-cloud/scripts
pip install -r requirements.txt
```

## 標準手順

### Step 1: パブリッシュ実行

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py \
  --twbx "outputs/{theme}/WOW2026 W{N}.twbx" \
  --output-dir "outputs/{theme}"
```

引数:
- `--twbx <path>` — アップロードする .twbx の絶対パスまたは相対パス（必須）
- `--output-dir <path>` — `tmp/publish-result.json` と `backup/` を置く出題フォルダ（必須）
- `--overwrite` — 同名ワークブックがあれば上書き（デフォルトは新規作成）
- `--project "<projectName>"` — 投稿先プロジェクト名（省略時は `.env` の `TABLEAU_PROJECT_NAME`）
- `--name "<workbookName>"` — Cloud上での表示名（省略時は .twbx のファイル名から拡張子を除いたもの）

### Step 2: 結果確認

成功すると `outputs/{theme}/tmp/publish-result.json` に次の形式で書き出される:

```json
{
  "ok": true,
  "workbookId": "...",
  "workbookName": "WOW2026 W19",
  "projectName": "WOW Challenges",
  "webpageUrl": "https://10ax.online.tableau.com/#/site/.../views/...",
  "createdAt": "2026-05-12T...Z",
  "overwrote": false
}
```

`webpageUrl` をブラウザで開いて Viz を目視確認する。`create-x-post` Skill が次に走るとこのJSONを読んでURLを投稿文に埋め込む。

## 安全策

- **事前バックアップ**: `--overwrite` 指定時、既存ワークブックを `outputs/{theme}/backup/<workbookName>.twbx` にダウンロードしてから上書き。
- **リトライ**: ネットワーク／一時的サーバーエラーで最大3回まで指数バックオフ（2s, 4s, 8s）。
- **エラー時**: バックアップは残し、`tmp/publish-result.json` に `ok: false` とエラー詳細を書き出す。

## ロールバック

上書きで問題が起きたら手動でリストア:

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py \
  --twbx "outputs/{theme}/backup/{workbookName}.twbx" \
  --output-dir "outputs/{theme}" --overwrite
```

## トラブルシュート

| 症状 | 確認点 |
|---|---|
| `signin failed (401)` | PAT が失効していないか。Cloudで再発行 |
| `project not found` | `TABLEAU_PROJECT_NAME` または `--project` が正しいか |
| `version not supported` | API バージョン不一致。`publish.py` の `--use-server-version` で自動調整される |
