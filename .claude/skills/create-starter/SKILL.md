---
name: create-starter
description: 完成版のワークブック(.twbx)から、初心者向けに配るスターター・ワークブックを生成する。渡すシート（または参加者に作らせるシート）を指定すると、残りのシートと、それだけが使う計算フィールドを依存の木で判定して削り、ダッシュボードには削ったシートと同じ大きさの空白を残す。共有フィルター・配色・書式はそのまま。「スターターを作って」「途中まで組んだワークブックを配りたい」「定番部分だけ渡す版を作って」「スターター・ワークブック」で使用。
---

# スターター・ワークブック生成

完成版 `.twbx` から、出題の定番部分までを組み終えたスターターを作る。参加者はスターターを開き、空白の場所に足りないシートを作って完成版に到達する。

## 入力と出力

- 入力: 完成版 `outputs/{theme}/refine/YYYYWNN.twbx`（`create-workbook` のループ最終回の版）と、渡すシートの指定
- 出力: `outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx` と、同じ場所の展開済み `.twb`。Cloud 名は `YYYYWNN Starter`
- `refine/` の既存ファイル（完成版、`publish-result.json`、`render/`）は上書きしない
- 前提: `create-workbook` の初回セットアップ（`lxml`）と、`publish-to-cloud` の前提（`.env` と認証）

## 手順

```
進捗:
- [ ] Step 1: 渡す範囲を決める
- [ ] Step 2: 生成する
- [ ] Step 3: 検証する（TWB・Cloud・Desktop）
- [ ] Step 4: 盲検する（任意）
- [ ] Step 5: 配布をユーザーに渡す
```

### Step 1: 渡す範囲を決める

範囲はシート単位で決める。計算フィールドはシートの選択から機械的に決まるので、個別には選ばない。

1. 完成版のシートを、定番の部分（スターターに入れる）と出題の核（参加者が作る）に分ける。手順書（`create-walkthrough`）がある回は、その第 1 部のシートを渡す
2. 判断に迷うシートは、次の 2 問で決める
   - 渡す計算だけで描けるか。描けるなら渡す
   - 参加者が新しい考え方を使うシートか。使うなら作らせる
3. dry-run で計画を出し、ユーザーに確認する

```bash
python .claude/skills/create-starter/scripts/build_starter.py \
  --twbx "outputs/{theme}/refine/YYYYWNN.twbx" \
  --remove "シートA,シートB" --dry-run
```

`--remove`（作らせるシート）と `--keep`（渡すシート）はどちらか一方を使う。出力の JSON で次を見せ、ユーザーの承認を得る:

- `kept_sheets` / `removed_sheets`: 渡すシートと作らせるシート
- `kept_calcs` / `removed_calcs`: 残る計算と、参加者が作る計算
- `blank_zones`: 空白にする場所と大きさ（px）。隣り合う削除シートは 1 つの空白にまとまる
- `removed_actions` / `edited_actions`: 削るシートが送り元・送り先のため消えるアクションと、除外リストからシート名だけを外したアクション
- `warnings`: 付け替え先の無いフィルター・凡例のゾーンや、サイズが固定でないレイアウトの空白

作らせる計算に新しい考え方が 1〜2 本だけ含まれ、残りが渡す計算の組み替えになっているのが目安。作らせる計算が多すぎる・少なすぎるときは、シートの分け方を見直す。

### Step 2: 生成する

```bash
python .claude/skills/create-starter/scripts/build_starter.py \
  --twbx "outputs/{theme}/refine/YYYYWNN.twbx" \
  --remove "シートA,シートB" \
  --out "outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx"
```

Cloud の公開版へのリンク（`repository-location`）はすべて消える。サイト名を公開物に残さないため。

終了コードが 2 のときは、`leftover_references`（削ったシート名・計算名が残っている箇所）か `warnings` がある。

- `warnings` が Step 1 で承認したものだけなら、そのまま Step 3 へ進む
- `leftover_references` は、出力の `.twb` を直してから詰め直す。`--twbx` にその `.twb`、`--remove ""`、同じ `--out` を指して再実行すると、データを同梱し直す

### Step 3: 検証する

**TWB**: XSD 検証と、完成版との要素比較を行う。

```bash
python .claude/skills/create-workbook/scripts/vendor/tableau-plugin/scripts/validate_workbook.py \
  "outputs/{theme}/refine/starter/YYYYWNN_Starter.twb"

python .claude/skills/create-starter/scripts/compare_workbooks.py \
  "outputs/{theme}/refine/YYYYWNN.twbx" "outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx" \
  --sheets "渡すシートをカンマ区切りで"
```

`compare_workbooks.py --sheets` は、残したシート・スターターにある計算・データソースのフィルターとセット・共有フィルターが完成版と同一かを確かめる。`same` 以外が出たら、スクリプトが残すものまで変えている。XSD 検証の無視してよい食い違いは `create-workbook` の [twb-pitfalls.md](../create-workbook/references/twb-pitfalls.md) にある。

**Cloud**: スターターを完成版と同じプロジェクトに上げ、描画する。結果が完成版の `refine/publish-result.json` と混ざらないよう、`--output-dir` に `refine/starter` を指す（結果は `refine/starter/refine/` に書かれる）。2 回目以降は `--overwrite` を付ける。

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py \
  --twbx "outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx" \
  --name "YYYYWNN Starter" \
  --output-dir "outputs/{theme}/refine/starter" --render --text-table
```

完成版の描画（`refine/render/`）と、ダッシュボードの PNG と文字の表（`*.text.tsv`）を並べて比べる:

- 残したシートのマークとラベルが、完成版と同じ位置に出る
- ラベルの値（文字の表の `text` 列）が、完成版と同じ値で出る
- 削ったシートの場所が空白になり、周囲のシートの位置がずれていない

`blank_zones` に `had_flexible_sheet: true` の空白があると、Cloud の描画では残したシートが数 px ずれることがある。空白は保存されたレイアウトの大きさで固定されるが、Cloud は伸縮するシートを保存時と違う大きさで描くため。値が一致し、ずれが数 px なら合格とし、Desktop での位置はユーザーに見てもらう。

完成版の `refine/publish-result.json` の `createdAt` が完成版 `.twbx` の更新より前なら、完成版の描画が古い。そのときは完成版も `--views` でダッシュボードだけ描画し直す。`refine/render/` の既存の描画が置き換わることを、先にユーザーに伝える。

フィルターを掛けた状態は PNG では比べられない。`refine/starter/refine/publish-result.json` の `webpageUrl` をチャットに出し、完成版とスターターで同じフィルターを選んで、残したシートが同じ形で出るかをユーザーに見てもらう。

**Desktop**: スターターを Tableau Desktop で開けることを、ユーザーに確かめてもらう。開くコマンド（`start outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx`）をチャットに出す。

### Step 4: 盲検する（任意）

スターター・要件・完成図だけで、足りない部分を組めるかをサブエージェントに試させる。要件のヒントが足りているかを見るための工程で、初めてスターターを配る回や、作らせる計算に新しい考え方が多い回に行う。

サブエージェント（`general-purpose`）には次だけを渡す。完成版と手順書は渡さない。

- スターターの中身（計算の式・各シートのシェルフとマーク・ダッシュボードの空白）。`analyze-twbx` の `structure.ts` と `calculated-fields.ts` の出力を `outputs/{theme}/tmp/starter-check/starter-spec.md` にまとめて渡す
- 要件（`requirements-{ja,en}.md`）
- 完成図（完成版のダッシュボードの PNG）

依頼は「足りないシートと計算を、式とシェルフの設定まで書き出す。詰まった箇所と、そこで欲しかったヒントを挙げる」とする。結果は `outputs/{theme}/tmp/starter-check/` に置く。完成版の式と照らし、詰まった箇所を要件のヒントの候補として `discussion.md` に書く。要件への反映は `create-requirements`（確定）で行う。

### Step 5: 配布をユーザーに渡す

- `discussion.md` に、渡したシート・計算の数、作らせるシート・計算の数、空白の大きさ、生成コマンドを追記する
- Tableau Public への公開はユーザーに頼む。公開する `.twbx` を開くコマンドと、Cloud の `webpageUrl` をチャットに出す。スターターはリポジトリに入れない（`*.twbx` は gitignore 済み）
- スターターではワークシートを非表示にしない。参加者がシートを開いて中身を読み、編集するため
- 要件の冒頭に、スターターの URL と「スターターを使わずに組んでもよい」旨を書くよう、`create-requirements`（確定）に引き継ぐ

## 制約

- 計算が要るかどうかは、残るもの（シート・ダッシュボード・アクション・共有フィルター・データソースのフィルター・セット・階層・抽出の条件）から式の参照をたどって決める。セットやデータソースのフィルターが使う計算は、どのシートが使わなくても残る
- 計算はデータソースごとに区別する。パラメータは削らない
- 空白の px は、保存されたゾーンの大きさとダッシュボード（デバイスレイアウトはそのレイアウト）の固定サイズから計算する。伸縮する空白にはしない。空のゾーンは、シートと同じ割合で余りの高さを受け取らないため。サイズが固定でないレイアウトでは空白も固定にならず、`warnings` に出る
- 浮動ゾーンは、削るシートごとに同じ位置・大きさの空白にする（まとめない）
- ストーリーポイントが削るシートを捉えているときは処理しない。`leftover_references` に出るので手で直す
