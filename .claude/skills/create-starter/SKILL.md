---
name: create-starter
description: 完成版のワークブック(.twbx)から、初心者向けに配るスターター・ワークブックを生成する。渡すシート（または参加者に作らせるシート）を指定すると、残りのシートと、それだけが使う計算フィールドを依存の木で判定して削り、ダッシュボードには削ったシートと同じ大きさの空白を残す。共有フィルター・配色・書式はそのまま。「スターターを作って」「途中まで組んだワークブックを配りたい」「定番部分だけ渡す版を作って」「スターター・ワークブック」で使用。
---

# スターター・ワークブック生成

完成版 `.twbx` から、出題の定番部分までを組み終えたスターターを作る。参加者はスターターを開き、空白の場所に足りないシートを作って完成版に到達する。上級者はスターターを使わず、データだけで組んでよい。

スターターはリポジトリに入れない（`*.twbx` は gitignore 済み）。Tableau Public への公開はユーザーが行う。

## 入力と出力

- 入力: 完成版 `outputs/{theme}/refine/YYYYWNN.twbx`（`create-workbook` のループ最終回の版）と、渡すシートの指定
- 出力: `outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx`（同じ場所に展開済みの `.twb` も置く）。Cloud 名は `YYYYWNN Starter`
- `refine/` の既存ファイル（完成版、`publish-result.json`、`render/`）は上書きしない

依存: `lxml`（`create-workbook` の XSD 検証と同じ。`pip install -r .claude/skills/create-workbook/scripts/vendor/tableau-plugin/scripts/requirements.txt`）

## 手順

```
進捗:
- [ ] Step 1: 渡す範囲を決める
- [ ] Step 2: 生成する
- [ ] Step 3: 検証する（TWB・Cloud の描画）
- [ ] Step 4: 盲検する（任意）
- [ ] Step 5: 配布をユーザーに渡す
```

### Step 1: 渡す範囲を決める

範囲はシート単位で決める。計算フィールドはシートの選択から機械的に決まるので、個別には選ばない。

1. 完成版のシートを、定番の部分（スターターに入れる）と出題の核（参加者が作る）に分ける。手順書（`create-walkthrough`）がある回は、その第 1 部のシートを渡す
2. 判断に迷うシートは、次の 2 問で決める
   - 定番の部分と同じ計算だけで描けるか。描けるなら渡す（例: 渡す帯と同じ集計を出すラベル）
   - 参加者が新しい考え方を使うシートか。使うなら作らせる
3. dry-run で計画を出し、ユーザーに確認する

```bash
python .claude/skills/create-starter/scripts/build_starter.py \
  --twbx "outputs/{theme}/refine/YYYYWNN.twbx" \
  --remove "シートA,シートB" --dry-run
```

`--remove`（作らせるシート）と `--keep`（渡すシート）はどちらか一方を使う。出力の JSON で次を見せ、ユーザーの承認を得る:

- `kept_sheets` / `removed_sheets`: 渡すシートと作らせるシート
- `kept_calcs` / `removed_calcs`: 残る計算と、参加者が作る計算。残すシートから式をたどって届く計算だけが残る
- `blank_zones`: 空白にする場所と高さ（px）。隣り合う削除シートは 1 つの空白にまとまる

作らせる計算に新しい考え方が 1〜2 本だけ含まれ、残りが渡す計算の組み替えになっているのが目安。作らせる計算が多すぎる・少なすぎるときは、シートの分け方を見直す。

### Step 2: 生成する

dry-run と同じ指定で `--out` を付けて実行する。

```bash
python .claude/skills/create-starter/scripts/build_starter.py \
  --twbx "outputs/{theme}/refine/YYYYWNN.twbx" \
  --remove "シートA,シートB" \
  --out "outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx"
```

スクリプトが行うこと:

- 削るシートの `<worksheet>`・`<window>`・サムネイル・ビューポイントを消す。削るシートが送り元・送り先のアクションも消す（`removed_actions` に出る）
- `removed_calcs` の計算と、それを指すデータソース内の要素（列インスタンス・フォルダ・色の割り当て）を消す
- ダッシュボードの削るシートのゾーンを、同じ位置・大きさの空白ゾーン（`type-v2='empty'`）に置き換える。縦・横のコンテナ内では固定サイズにし、px をダッシュボードのサイズから計算する
- 削るシートに付いたフィルター・凡例のゾーンは、同じフィールドを使う残すシートに付け替える。付け替え先が無ければ消して `warnings` に出す
- Cloud の公開版へのリンク（`repository-location`）をすべて消す。サイト名が公開物に残らないようにするため
- 計算・シート・共有フィルター（`<shared-views>`）・配色・書式には、ほかに手を加えない。データ（抽出）は完成版のものを同梱する

終了コードが 2 のときは、`leftover_references`（削ったはずの計算名・シート名が残っている箇所）か `warnings` がある。残った参照は TWB を開いて当該要素を直し、もう一度検証する。

### Step 3: 検証する

3 つとも通ったら Step 4 へ進む。

**TWB の検証**: XSD 検証と、完成版との要素比較を行う。

```bash
python .claude/skills/create-workbook/scripts/vendor/tableau-plugin/scripts/validate_workbook.py \
  "outputs/{theme}/refine/starter/YYYYWNN_Starter.twb"

python .claude/skills/create-starter/scripts/compare_workbooks.py \
  "outputs/{theme}/refine/YYYYWNN.twbx" "outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx" \
  --sheets "渡すシートをカンマ区切りで"
```

`compare_workbooks.py --sheets` は、残したシートと計算が完成版と XML 上で同一であることを確かめる。`same` 以外が出たら、スクリプトが残すシートまで変えている。XSD 検証の無視してよい食い違いは `create-workbook` の [twb-pitfalls.md](../create-workbook/references/twb-pitfalls.md) にある。

**Cloud の描画**: スターターを `YYYYWNN Starter` として完成版と同じプロジェクトに上げ、描画する。結果の置き場が完成版と混ざらないよう、`--output-dir` に `refine/starter` を指す（結果は `refine/starter/refine/` に書かれる）。

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py \
  --twbx "outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx" \
  --name "YYYYWNN Starter" \
  --output-dir "outputs/{theme}/refine/starter" --render --text-table
```

2 回目以降は `--overwrite` を付ける。完成版の描画（`refine/render/`）と、ダッシュボードの PNG と文字の表（`*.text.tsv`）を並べて比べる:

- 残したシートの帯・棒・ラベルが、完成版と同じ位置に出る
- ラベルの値（文字の表の `text` 列）が、完成版と同じ値で出る
- 削ったシートの場所が空白になり、その上下のシートの位置がずれていない

完成版の描画が古いときは、完成版も `--views` でダッシュボードだけ描画し直す。そのときは `refine/` の既存の描画が置き換わることをユーザーに伝える。

フィルターを掛けた状態の比較は PNG ではできない。`refine/starter/refine/publish-result.json` の `webpageUrl` をチャットに出し、完成版とスターターで同じフィルター（例: 件数の少ない組み合わせ）を選んで、残したシートが同じ形で出るかをユーザーに見てもらう。

**Desktop で開く**: スターターを Tableau Desktop で開けることをユーザーに確かめてもらう。開くコマンドをチャットに出す（`start outputs/{theme}/refine/starter/YYYYWNN_Starter.twbx`）。

### Step 4: 盲検する（任意）

スターター・要件・完成図だけで、足りない部分を組めるかをサブエージェントに試させる。要件のヒントが足りているかを見るための工程で、初めてスターターを配る回や、作らせる計算に新しい考え方が多い回に行う。

サブエージェント（`general-purpose`）には次だけを渡す。完成版と手順書は渡さない。

- スターターの中身（計算の式・各シートのシェルフとマーク・ダッシュボードの空白）。`analyze-twbx` の `structure.ts` と `calculated-fields.ts` の出力を `outputs/{theme}/tmp/starter-check/starter-spec.md` にまとめて渡す
- 要件（`requirements-{ja,en}.md`）
- 完成図（完成版のダッシュボードの PNG）

依頼は「足りないシートと計算を、式とシェルフの設定まで書き出す。詰まった箇所と、そこで欲しかったヒントを挙げる」とする。結果は `outputs/{theme}/tmp/starter-check/` に置き、完成版の式と照らして、詰まった箇所を要件のヒントの候補として `discussion.md` に書く。要件への反映は `create-requirements`（確定）で行う。

### Step 5: 配布をユーザーに渡す

- `discussion.md` に、渡したシート・計算の数、作らせるシート・計算の数、空白の高さ、生成コマンドを追記する
- Tableau Public への公開はユーザーに頼む。公開する `.twbx` を開くコマンドと、Cloud の `webpageUrl` をチャットに出す
- スターターではワークシートを非表示にしない。参加者がシートを開いて中身を読み、編集するため
- 要件の冒頭（Introduction か Requirements の最初）に、スターターの URL と「スターターを使わずに組んでもよい」旨を書くよう、`create-requirements`（確定）に引き継ぐ

## 制約

- 計算フィールドの依存は式の中の `[内部名]` でたどる。パラメータは削らない（使われなくなったパラメータが残る）
- フィルター・凡例のゾーンの付け替えは、同じフィールドのインスタンス名を使うシートを探す。見つからないときは手で直す
- 浮動ゾーンは、削るシートごとに同じ位置・大きさの空白にする（まとめない）
