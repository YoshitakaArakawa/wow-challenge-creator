---
name: create-walkthrough
description: 完成したWOWのTableauワークブック1つから、参加者が描画で確かめながら1段ずつ作り進める手順書(guide/walkthrough-{ja,en}.html)を作る。TWBから計算の依存の木・表計算の方向・並べ替え・書式を抜き出して章立て(第1部は定番、第2部は出題の核)を設計し、承認を取ってから、シート単体の描画・ダッシュボード上の位置の枠付き画像・照合した確認の値を埋め込んだ日本語版と英語版を書き、GitHub Pagesに載せる。「手順書を作って」「ウォークスルーを作って」「作り方の解説を作って」「解き方をステップごとにまとめて」「参加者向けのヒントのページ」「walkthroughを作って」で使用。要件文やIntroの作成には使わない(create-requirements)。
---

# 手順書（walkthrough）作成スキル

完成版のワークブック 1 つだけを入力に、参加者がデータから完成版までを章ごとに作る手順書を作る。出力は `outputs/{theme}/guide/walkthrough-ja.html` と `walkthrough-en.html`（画像埋め込みの 1 ファイル）で、GitHub Pages で公開される。

## 規範

- **章 = 描画で確かめられる中間成果 1 つ**: 既定はシート 1 枚で 1 章。ただし次の 2 つは例外にする
  - 新しく作る計算が多すぎるシート（目安 6 本超）は、計算の依存の木の節（マークの層、デュアル軸の片側など）で章を分ける
  - 新しい計算が要らないシート（複製して差し替えるだけのシート）は、複製元の章の手順にする
- **章立ては承認を取ってから書く**: Step 2 の表で確定する。HTML を書き始めてから組み替えない
- **事実は抽出と照合から取る**: 式・シェルフ・方向・並べ替え・書式は `twb-spec.md` から転記する。本文に書く数値と主張（値・並び・フィルターの組み合わせの結果）は、照合スクリプトの出力から取る。描画は突き合わせにだけ使う
- **ヒントが先、答えが後**: ヒントには考え方を 1〜3 項目だけ書き、式は答えに置く。答えは折りたたまない
- **入力は完成版だけ**: スターターや作業途中のファイルは読まない。開始点の既定は「データだけから全部作る」
- **公開前提**: 実プロジェクト名・Cloud のサイト名・URL・個人パス・メールアドレス・作業フォルダのパスを書かない（`build_walkthrough.py` が検出する）
- **文体**: 結論を先に置き、一文に主張を 1 つだけ書く。フィールド名・シート名・シェルフ名は英語のまま書く

## 入力と出力

- 入力: 最終 publish した `.twbx`（`refine/publish-result.json` の `source`）。Cloud で直された場合は `analyze-twbx` の Cloud 経路で pull したもの
- 中間物: すべて `outputs/{theme}/tmp/walkthrough/` に置く
- 出力: `outputs/{theme}/guide/walkthrough-ja.html`・`walkthrough-en.html`

## 依存

- Python 3.10+、`Pillow`、publish-to-cloud の依存（`pip install -r .claude/skills/publish-to-cloud/scripts/requirements.txt`）
- 照合で同梱データを読むために、`.hyper` なら `tableauhyperapi`、Excel なら `pandas`・`openpyxl`
- Google Chrome（撮影）

## 手順

```
進捗:
- [ ] Step 1: 完成版を抽出する
- [ ] Step 2: 章立てを設計し、承認を取る
- [ ] Step 3: 図の素材を描画する
- [ ] Step 4: 確認の値を算出する
- [ ] Step 5: 日本語版を書く
- [ ] Step 6: 英語版を書く
- [ ] Step 7: 組み立てて検査する
- [ ] Step 8: Pages に載せる
```

### Step 1: 完成版を抽出する

```bash
python ${CLAUDE_SKILL_DIR}/scripts/extract_twb.py <final>.twbx --json tmp/walkthrough/twb-spec.json --md tmp/walkthrough/twb-spec.md
```

`twb-spec.md` を通読する。項目の意味はスクリプトの docstring にある。

### Step 2: 章立てを設計し、承認を取る

```bash
python ${CLAUDE_SKILL_DIR}/scripts/plan_chapters.py tmp/walkthrough/twb-spec.json [--order "A,B,..."] [--given "X"] --md tmp/walkthrough/chapters.md
```

シートごとに、作る計算・前のシートから使う計算・ディメンション・ダイアログで決める方向が出る（並びは `--order`、なければダッシュボード順）。これを材料に、次の順で章を決める。

1. 依存の上流から下流へ並べる。式の複製や差し替えで作れる章は、元の章の直後に置く
2. 規範の「章 = 中間成果 1 つ」に沿って、シートを分ける・まとめる
3. 第 1 部（定番の手法で作れる部分）と第 2 部（この出題の核。普通の作り方にない計算）に分ける。第 2 部の最初の章に核を置く。核がない出題は部に分けない
4. 先頭に章 0「データをつなぐ」、末尾に終章「ダッシュボードに並べる」を置く

ユーザーには章の表（章・作るもの・作る計算・新しい考え方・部）を見せて承認を取る。Step 5 は承認の後に始める。Step 3・4 は並行してよい。

**スターターを配る回**: スターター（`create-starter` で作る）が配るシートを `--given` に渡す。第 1 部は「土台を読む」1 章に畳み、配った計算を役割のまとまりごとに表で示す。第 2 部で使い方を変える計算があれば、その違いを確かめさせる。

### Step 3: 図の素材を描画する

検証用ワークブックを 2 つ作る（完成版は書き換えない）。

```bash
python ${CLAUDE_SKILL_DIR}/scripts/sheet_figures.py make <final>.twbx tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets.twbx
```

2 つとも、完成版と同じプロジェクト（`refine/publish-result.json` の `projectName`）に別名で上げ、描画する。完成版のダッシュボードの描画がまだなければ、同様に `--render --views` で撮る。

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py --twbx tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets.twbx \
  --output-dir tmp/walkthrough/sheets --project "<projectName>" --name "<YYYYWNN> Walkthrough Sheets" --overwrite --render
python .claude/skills/publish-to-cloud/scripts/publish.py --twbx tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets_Frames.twbx \
  --output-dir tmp/walkthrough/frames --project "<projectName>" --name "<YYYYWNN> Walkthrough Frames" --overwrite --render --views "<Dashboard>"
python ${CLAUDE_SKILL_DIR}/scripts/sheet_figures.py frame --render <完成版のダッシュボードの描画> \
  --marked tmp/walkthrough/frames/refine/render/<Dashboard>.png \
  --zones tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets_Frames.zones.json --out-dir tmp/walkthrough/figs
```

- シート単体の描画（`sheets/refine/render/<シート>.png`）は、各章の「ゴールのシート」に使う。`make` が `axes shown: none` と出したら、図の説明に軸の注記を付けない
- `ctx-<シート>.png` はゴールのシートの上に置く。ダッシュボードのシートが 1 枚なら作らない
- フィルターをかけた状態の図が要るときだけ、`render_states.py` を使う
- 描画した PNG は Read で開き、枠の位置とシートの見た目を確かめる

### Step 4: 確認の値を算出する

各章の「この値が出れば正解」を、同梱データから再計算するスクリプト `tmp/walkthrough/check_values.py` を書く。

- データは `.twbx` の同梱ファイルを zip から読む。データソースのすべての表（補助の表を含む）の中身も出し、章 0 で使う
- 計算は TWB の式をそのまま移す。表計算は、そのシートの方向と並べ替えの順で計算する
- 章ごとに、その章のビューのディメンションの粒度で出す
- 数値は、完成版の表示書式（`twb-spec.md` の既定の数値書式）に合わせて丸める
- 出力をシート単体の描画（軸目盛り・マークの端・ラベル）と突き合わせる。合わなければ、式か方向の写し間違いを直してから進む

### Step 5: 日本語版を書く

[assets/walkthrough-template.html](assets/walkthrough-template.html) を `tmp/walkthrough/walkthrough-ja.src.html` にコピーして埋める。テンプレートの部品だけを使う。

節の順: ヘッダー → 全体（ダッシュボードの並びと章の表）→ 章 0 → 第 1 部 → 第 2 部 → 終章 → フッター。

章の型（どの章も同じ順）:

1. **ゴールのシート**: 枠付き画像、シェルフとマークカードの模式図、シート単体の描画。その章で作るピルに印を付ける
2. **このシートのディメンション**: 置く場所と役割の表。置かないディメンションも理由と一緒に書く
3. **部品の分解図**: `twb-spec.md` の部品の木から、その章に要る範囲を描く。作る計算に手順番号、前の章の計算に章番号を付ける
4. **手順**: 計算 1〜2 本ごとに「目的 → ヒント → 答え → 確認の値」。最後に「シートを組む」手順（方向のダイアログ、既定と違う設定）を置き、確認の値で締める

書き方の原則:

- **設定は漏れなく載せる**: `twb-spec.md` のそのシートの節にある設定は、どれかの章の手順か終章に必ず載せる。対象は、並べ替えとそれに使う計算、軸、ペインの書式、色の割り当て、計算の既定の数値書式、データの役割と集計の変更。シートを複製させる章では、複製元との差分を全部書く
- **ダイアログは抽出どおりに描く**: ピルごとの入れ子の一覧（`twb-spec.md` の「表計算 `<ピル>`」）どおりに描く。方向が「特定のディメンション」の入れ子だけを番号付きで描き、残りは「既定のまま」とまとめる
- **見えない値は検算シートで確かめる**: 表計算の値が画面に出ない章と、前の章の表計算を別の方向で使い直す章では、検算用のテキスト表で値を確かめる手順を置く

### Step 6: 英語版を書く

日本語版のソースを `walkthrough-en.src.html` にコピーし、構造と画像はそのままに本文を訳す。`<html lang="en">` にする（フォントは CSS が切り替える）。UI 語と部品の見出しは [references/ui-terms.md](references/ui-terms.md) に従う。表にない UI 語は、英語版 Tableau の表記を確かめて表に足す。

### Step 7: 組み立てて検査する

```bash
python ${CLAUDE_SKILL_DIR}/scripts/build_walkthrough.py --theme-dir outputs/{theme} --lang ja --shoot tmp/walkthrough/shots
python ${CLAUDE_SKILL_DIR}/scripts/build_walkthrough.py --theme-dir outputs/{theme} --lang en --shoot tmp/walkthrough/shots
```

- `ERROR` が出たらソースを直して再実行する。`WARN`（作業フォルダへの言及）も消す
- 撮影の切れ端を Read で順に見て、崩れ・空の `{{`・375px 幅でのページ全体の横スクロールがないことを確かめる
- `twb-spec.md` の各シートの節と本文を照らし、載っていない設定がないことを確かめる

### Step 8: Pages に載せる

リポジトリ直下の `index.html` の一覧の先頭に、既存のカードの構造を写して出題のカードを 1 枚足す。リンク先は `outputs/{theme}/guide/walkthrough-{ja,en}.html` にする。出題フォルダ名を変えると URL も変わるので、フォルダ名の確定後に載せる。`discussion.md` に、章立てと公開先を追記する。

## 参照

- テンプレートと部品: [assets/walkthrough-template.html](assets/walkthrough-template.html)
- 英語版の UI 語: [references/ui-terms.md](references/ui-terms.md)
