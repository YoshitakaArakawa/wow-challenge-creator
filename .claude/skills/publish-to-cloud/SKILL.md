---
name: publish-to-cloud
description: 生成済みの.twbxをTableau Cloudにパブリッシュし、必要なら全ビューをPNGに描画して保存する。OAuthブラウザサインイン(PATも可)、上書き対応、上書き時の事前バックアップ、指数バックオフリトライ。「Cloudにパブリッシュして」「TWBXをアップロード」「ワークブックを公開」「publishして表示を確認」で使用。
---

# Tableau Cloud パブリッシュスキル

`create-workbook` で生成した、または手動で配置した `.twbx` を Tableau Cloud にアップロードする。`--render` を付けると publish 直後に各ビューの PNG を取り、Claude が描画結果を直接読める。

## 命名規約

- Cloud 上のワークブック名は `YYYYWNN`（例: `2026W40`）。WOW の週番号を 2 桁ゼロ埋めし、タイトルは付けない
- `.twbx` のファイル名も同じ `YYYYWNN.twbx` にする。`--name` 省略時はファイル名の拡張子を除いた部分が Cloud 名になるので、両者が一致する
- 投稿先プロジェクトは `.env` の `TABLEAU_PROJECT_NAME`（既定 `99_WorkoutWednesday`）。名前一致で探すので、同名プロジェクトをサイト内に複数作らない

## 前提

リポジトリ直下の `.env` に接続先が設定されていること（[`.env.example`](../../../.env.example) 参照）:

```
TABLEAU_SERVER_URL=https://example.online.tableau.com
TABLEAU_SITE_ID=
TABLEAU_PROJECT_NAME=99_WorkoutWednesday
```

認証は OAuth 2.0（Authorization Code + PKCE）のブラウザサインイン。`.env` にトークンは置かない。初回、またはセッション失効時に次を実行し、開いたブラウザでユーザーにサインインしてもらう:

```bash
python .claude/skills/publish-to-cloud/scripts/tableau_auth.py login
```

- セッションは `.auth-cache/session.json`（gitignore 済み）に保存され、`publish.py` と analyze-twbx の Cloud 経路が共用する
- `tableau_auth.py status` で生存確認（exit 0 なら有効）、`logout` でサーバー側サインアウトとキャッシュ削除
- `.env` に `TABLEAU_PAT_NAME` と `TABLEAU_PAT_VALUE` を両方置くと PAT 認証に切り替わる（キャッシュは使わない）

初回のみ依存をインストール:

```bash
cd .claude/skills/publish-to-cloud/scripts
pip install -r requirements.txt
```

## 標準手順

### Step 1: パブリッシュ実行

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py \
  --twbx "outputs/{theme}/refine/2026W40.twbx" \
  --output-dir "outputs/{theme}" --render
```

引数:
- `--twbx <path>` — アップロードする .twbx の絶対パスまたは相対パス（必須）
- `--output-dir <path>` — 出題フォルダ `outputs/{theme}`（必須）。結果はすべてその下の `refine/` に書く
- `--overwrite` — 同名ワークブックがあれば上書き（デフォルトは新規作成）
- `--project "<projectName>"` — 投稿先プロジェクト名（省略時は `.env` の `TABLEAU_PROJECT_NAME`）
- `--name "<workbookName>"` — Cloud上での表示名（省略時は .twbx のファイル名から拡張子を除いたもの）
- `--render` — publish 後に全ビューを High 解像度 PNG で `outputs/{theme}/refine/render/<view>.png` に保存（前回の PNG は消す）
- `--views "A,B"` — `--render` の対象ビューを名前で絞る（省略時は全ビュー。ダッシュボードだけ見たいときに使う）

### Step 2: 結果確認

成功すると `outputs/{theme}/refine/publish-result.json` に次の形式で書き出される:

```json
{
  "ok": true,
  "workbookId": "...",
  "workbookName": "2026W40",
  "projectName": "99_WorkoutWednesday",
  "webpageUrl": "https://example.online.tableau.com/#/site/.../workbooks/...",
  "createdAt": "2026-10-01T...Z",
  "overwrote": false,
  "backupPath": null,
  "source": "outputs/{theme}/refine/2026W40.twbx",
  "renders": [
    {"viewName": "Dashboard", "viewId": "...", "filePath": "outputs/{theme}/refine/render/Dashboard.png"}
  ]
}
```

`renders[].filePath` を Read で開けば描画結果を Claude が直接見られる。`--render` なしのときは `renders` は `null`。`create-x-post` Skill が次に走るとこのJSONを読んで `webpageUrl` を投稿文に埋め込む。

## 編集 → publish → 確認のループ

TWB を編集しながら表示を追うときは、`publish.py` を直接呼ばず create-workbook Skill の Step 5（`iterate.ts`）で回す。検証 → repack → `publish.py --overwrite --render` を 1 コマンドで行う。ループの回し方と比較ページの使い方もそこにある。

## 安全策

- **事前バックアップ**: `--overwrite` 指定時、既存ワークブックを `outputs/{theme}/refine/backup/<workbookName>.twbx` にダウンロードしてから上書き。
- **リトライ**: ネットワーク／一時的サーバーエラーで最大3回まで指数バックオフ（2s, 4s, 8s）。
- **エラー時**: バックアップは残し、`refine/publish-result.json` に `ok: false` とエラー詳細を書き出す。

## ロールバック

上書きで問題が起きたら手動でリストア:

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py \
  --twbx "outputs/{theme}/refine/backup/{workbookName}.twbx" \
  --output-dir "outputs/{theme}" --overwrite
```

## トラブルシュート

| 症状 | 確認点 |
|---|---|
| `No cached Tableau Cloud session` / `session expired` | `tableau_auth.py login` を実行し、ブラウザでサインインしてもらう |
| `signin failed (401)` | PAT 認証時のみ。PAT が失効していないか。Cloudで再発行 |
| `project not found` | `TABLEAU_PROJECT_NAME` または `--project` が正しいか |
| `version not supported` | API バージョン不一致。`publish.py` はサーバーの版に自動で合わせるので、`tableauserverclient` を更新する |
| `--render` の PNG が前回と同じ | Cloud の画像キャッシュ（`--render` は最小の `maxAge` 1 分で取得する）。1 分待って再 publish する |
| `views could not be listed` | publish 直後の反映待ち。`publish.py` は 3 秒間隔で 5 回まで待つので、超えたら再実行する |
| publish は通るが PNG が空白 | Desktop で開いたときも空白になる構文。create-workbook の `references/twb-pitfalls.md` で当たる |
