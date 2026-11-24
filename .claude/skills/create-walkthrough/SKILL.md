---
name: create-walkthrough
description: 完成したWOWのTableauワークブック1つから、参加者が1シートずつ作り進める手順書(guide/walkthrough-{ja,en}.html)を作る。TWBから計算の依存の木・表計算の方向・並べ替えを抜き出して章立て(作るシート1枚=1章、第1部は定番、第2部は出題の核)を設計し、承認を取ってから、シート単体の描画・ダッシュボード上の位置の枠付き画像・照合した確認の値を埋め込んだ日本語版と英語版を書き、GitHub Pagesに載せる。「手順書を作って」「ウォークスルーを作って」「作り方の解説を作って」「解き方をステップごとにまとめて」「参加者向けのヒントのページ」「walkthroughを作って」で使用。要件文やIntroの作成には使わない(create-requirements)。
---

# 手順書（walkthrough）作成スキル

完成版のワークブック 1 つだけを入力に、参加者がデータから完成版までを 1 シートずつ作る手順書を作る。出力は `outputs/{theme}/guide/walkthrough-ja.html` と `walkthrough-en.html` の 2 ファイル（画像埋め込みの 1 ファイル完結）で、GitHub Pages で公開される。

## 規範

- **章 = 作るシート 1 枚**: 計算はそれを初めて要る章で作り、後の章では「前の章で作ったもの」として参照する。章の型（ゴールのシート → ディメンション → 部品の分解図 → 手順 → 確認）は崩さない
- **章立てはユーザーの承認を取ってから書く**: Step 2 の表を見せて確定する。HTML を書き始めてから章を組み替えない
- **事実は TWB と描画から取る**: 式・シェルフ・方向・並べ替え・軸の設定は `extract_twb.py` の出力から転記する。描画から推測しない
- **数値は照合スクリプトで出してから載せる**: 確認の値は Step 4 のスクリプトの出力で、描画と突き合わせたものだけを書く
- **ヒントが先、答えが後**: ヒントには考え方だけを書き、式は答えに置く。答えは折りたたまずに常に表示する
- **入力は完成版だけ**: スターターや作業途中のファイルは読まない。開始点の既定は「データだけから全部作る」
- **公開前提**: 実プロジェクト名・Cloud のサイト名・URL・個人パス・メールアドレス・作業フォルダのパスを本文に書かない。`build_walkthrough.py` が検出して書き出しを止める
- **明るい配色に固定する**: Tableau の描画が白背景のため。テンプレートの CSS をそのまま使う
- **文体**: 日本語は CLAUDE.md の個人ルール（一文一義、結論先行）に従う。フィールド名・シート名・シェルフ名は英語のまま書く。英語版の UI 語は [references/ui-terms.md](references/ui-terms.md) に従う

## 入力と出力

パスは `outputs/{theme}/` から。

| 種類 | パス |
|---|---|
| 入力: 完成版 | 最終 publish した `.twbx`（`refine/publish-result.json` の `source`）。Cloud で直された場合は `analyze-twbx` の Cloud 経路で pull したもの |
| 中間: 抽出結果 | `tmp/walkthrough/twb-spec.json`・`twb-spec.md` |
| 中間: 章立て | `tmp/walkthrough/chapters.md` |
| 中間: 検証用ワークブック | `tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets.twbx`（軸を表示）・`_Frames.twbx`（ゾーンに色枠）・`_Frames.zones.json` |
| 中間: 図 | `tmp/walkthrough/figs/`（`dash-*.png`・`ctx-*.png`）、`tmp/walkthrough/sheets/refine/render/<シート>.png` |
| 中間: 照合 | `tmp/walkthrough/check_values.py` と出力 |
| 中間: HTML ソース | `tmp/walkthrough/walkthrough-{ja,en}.src.html`（画像は `embed:` 参照） |
| 出力 | `guide/walkthrough-ja.html`・`guide/walkthrough-en.html` |

出題フォルダの中身は gitignore の対象なので、ワークツリーで作業するとそこにはない。その場合は、出題フォルダがあるチェックアウトのパスをスクリプトに渡し、中間物もその出題フォルダに書く。

パイプライン上は、`create-workbook` の refine ループが終わった後に使う。要件の確定（`create-requirements`）の前でも後でもよい。

## 依存

- Python 3.10+、`Pillow`、`tableauserverclient`・`python-dotenv`（`publish-to-cloud` と同じ。`pip install -r .claude/skills/publish-to-cloud/scripts/requirements.txt`）
- 照合スクリプトで同梱データを読むために、`.hyper` なら `tableauhyperapi`、Excel なら `pandas`・`openpyxl`
- Google Chrome（Step 7 の撮影）

## 手順

```
進捗:
- [ ] Step 1: 完成版を抽出する
- [ ] Step 2: 章立てを設計し、承認を取る
- [ ] Step 3: 図の素材を描画する
- [ ] Step 4: 確認の値を算出し、描画と突き合わせる
- [ ] Step 5: 日本語版を書く
- [ ] Step 6: 英語版を書く
- [ ] Step 7: 組み立てて検査し、撮影する
- [ ] Step 8: Pages に載せる
```

### Step 1: 完成版を抽出する

```bash
python ${CLAUDE_SKILL_DIR}/scripts/extract_twb.py outputs/{theme}/<final>.twbx \
  --json outputs/{theme}/tmp/walkthrough/twb-spec.json --md outputs/{theme}/tmp/walkthrough/twb-spec.md
```

`twb-spec.md` を読む。章を書くときに使う項目:

- 計算フィールド: 式、`kind`（`row` 行レベル / `agg` 集計 / `tc` 表計算 / `tc-derived` 表計算を参照 / `lod`）、参照・被参照、使うシート
- シートごと: Rows・Columns のピル（連続/不連続、△）、マークカードの並び、入れ子の表計算の方向と順序、並べ替え、軸の固定と反転、ラベルの編集、ビューにあるディメンション、部品の木、要る計算（葉から）
- データソース全体のフィルター（全シートに効く）、共有フィルター、色の割り当て、ダッシュボードのゾーン

### Step 2: 章立てを設計し、承認を取る

下書きを出す。`--order` なしだと「新しく作る計算の少ない順」に並ぶ。

```bash
python ${CLAUDE_SKILL_DIR}/scripts/plan_chapters.py outputs/{theme}/tmp/walkthrough/twb-spec.json \
  [--order "Sheet A,Sheet B,..."] [--given "Sheet X"] --md outputs/{theme}/tmp/walkthrough/chapters.md
```

下書きを次の基準で並べ替え、`--order` を付けて出し直す。

1. 依存の上流から下流へ。下流のシートの計算を材料にするシートは後に置く
2. 新しい考え方の少ない章を先に置く。式の複製や番号の差し替えで作れる章は、元の章の直後に置く
3. 第 1 部と第 2 部に分ける。第 1 部は定番の手法（参考ワークブックや既知のチャートの作り方）で作れる部分、第 2 部はこの出題の核（普通の作り方にない計算）を含む部分。第 2 部の最初の章に核を置く
4. ダッシュボードの並び順とは別に決める。並び順は全体の節で図にする
5. 章 0「データをつなぐ」を先頭に、終章「ダッシュボードに並べる」を末尾に置く。終章には、ダッシュボードのサイズ・並び・データソース全体のフィルター・章で触れなかった書式をまとめる

ユーザーには、章の表（章・作るシート・作る計算・新しい考え方・第 1 部か第 2 部か）を見せて承認を取る。承認が出るまで Step 5 に進まない（Step 3・4 は並行してよい）。

**土台を配る回**: 出題者がスターター（第 1 部までのワークブック。`create-starter` で作る）を配るなら、配るシートを `--given` に渡す。スターターより先に章立てを決めた回は、第 1 部のシートがそのままスターターの範囲になる。第 1 部の章は書かず、「土台を読む」章 1 つに畳む。この章では、配った計算を役割のまとまりごとに表で示し（式・使われる場所・フィルターなしの値）、表計算の方向で値が変わることを、配ったシートのダイアログで確かめさせる。

### Step 3: 図の素材を描画する

検証用ワークブックを完成版から作る。完成版は書き換えない。

```bash
python ${CLAUDE_SKILL_DIR}/scripts/make_sheet_views.py outputs/{theme}/<final>.twbx \
  outputs/{theme}/tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets.twbx
```

- `<YYYYWNN>_WalkthroughSheets.twbx`: 全シートの軸を表示した版。シート単体の描画に使う
- `<YYYYWNN>_WalkthroughSheets_Frames.twbx`: ダッシュボードの各シートのゾーンに固有色の枠を付けた版。Cloud は描画時にゾーンの高さを組み直すので、保存された座標ではなく、この色の位置からシートの場所を取る

2 つとも、完成版と同じプロジェクト（`refine/publish-result.json` の `projectName`）に別名で上げ、描画する。

```bash
python .claude/skills/publish-to-cloud/scripts/publish.py --twbx outputs/{theme}/tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets.twbx \
  --output-dir outputs/{theme}/tmp/walkthrough/sheets --project "<projectName>" --name "<YYYYWNN> Walkthrough Sheets" --overwrite --render
python .claude/skills/publish-to-cloud/scripts/publish.py --twbx outputs/{theme}/tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets_Frames.twbx \
  --output-dir outputs/{theme}/tmp/walkthrough/frames --project "<projectName>" --name "<YYYYWNN> Walkthrough Frames" --overwrite --render --views "<Dashboard>"
```

完成版のダッシュボードを描画し、枠付き画像を作る。

```bash
python ${CLAUDE_SKILL_DIR}/scripts/render_states.py --theme-dir outputs/{theme} --view "<Dashboard>" \
  --out-dir tmp/walkthrough/figs --prefix dash- --state all
python ${CLAUDE_SKILL_DIR}/scripts/frame_context.py --render outputs/{theme}/tmp/walkthrough/figs/dash-all.png \
  --marked outputs/{theme}/tmp/walkthrough/frames/refine/render/<Dashboard>.png \
  --zones outputs/{theme}/tmp/walkthrough/sheets/<YYYYWNN>_WalkthroughSheets_Frames.zones.json --out-dir outputs/{theme}/tmp/walkthrough/figs
```

- シート単体の描画は `tmp/walkthrough/sheets/refine/render/<シート>.png`（空白は `_`）。「ゴールのシート」と「手順を終えた画面」に使う
- `ctx-<シート>.png` は「ゴールのシート」の上に置く
- フィルターの状態ごとの描画が要るときは、`render_states.py` に `--publish-result tmp/walkthrough/sheets/refine/publish-result.json` を付けてシートを描画する。フィルターをすべて選んだ状態は、全値を列挙して指定する
- サインインが切れていると `publish.py` が失敗する。`python .claude/skills/publish-to-cloud/scripts/tableau_auth.py login` を流し、ブラウザでのサインインをユーザーに頼む
- 描画した PNG は Read で開き、枠の位置とシートの見た目を確かめる

### Step 4: 確認の値を算出し、描画と突き合わせる

各章の「この値が出れば正解」を、同梱データから再計算するスクリプトを `tmp/walkthrough/check_values.py` に書く。

- データは `.twbx` に同梱されたファイル（`twb-spec.md` の「同梱ファイル」）を zip から読む。抽出（`.hyper`）なら一時フォルダに取り出して `tableauhyperapi` で読む
- 補助テーブル（Scaffold など）の中身も出す。章 0 で表にするため
- 計算は TWB の式をそのまま Python に移す。表計算は、そのシートの方向（順序）で並べてから累積・合計する。各ディメンションの中の順は、そのシートの並べ替え（手動ならその順、計算の並べ替えならその値の順）に従う
- 章ごとに、その章のビューのディメンションの粒度で出す。検算シート（テキスト表）を使う章は、検算シートのディメンションで出す
- 出力を描画と突き合わせる: シート単体の描画の軸目盛りと、帯・棒の端の位置、ラベルの金額が合うこと。合わなければ、式の写し間違いか方向の違いかを確かめてから先に進む
- 積み上げの並び（どの値がどちらの端に来るか）は、並べ替えと方向から算出し、描画で確かめてから書く。描画だけを見て書かない
- フィルターの組み合わせに触れる文（「〜で純額が負になる」など）を書くなら、その組み合わせもスクリプトで出す
- 0〜1 の割合は小数 3 桁、金額は整数ドルに丸める
- Windows では先頭で `sys.stdout.reconfigure(encoding="utf-8")` を呼ぶ

### Step 5: 日本語版を書く

[assets/walkthrough-template.html](assets/walkthrough-template.html) を `tmp/walkthrough/walkthrough-ja.src.html` にコピーし、`{{...}}` を埋める。テンプレートの部品だけを使い、新しい CSS を足さない（色は `--c1`・`--c2` に色の割り当てを入れる）。

構成（必ずこの順）:

| 節 | 内容 |
|---|---|
| ヘッダー | 題名、作るものの 1〜2 文、数のバッジ |
| 全体 | 完成版のダッシュボード、シートの並び（`.stack`）、章の表、ピルの凡例 |
| 章 0 | データをつなぐ: 表の結び方（リレーションシップ）、補助テーブルの中身、データソース全体のフィルターの付け方 |
| 第 1 部の扉・章 | 定番部分。章の型で書く |
| 第 2 部の扉・章 | 出題の核。最初の章で `.core` の囲みに「新しく考えるのはここ」を 1〜2 文で書く |
| 終章 | ダッシュボードに並べる（サイズ・並び・余白・フィルターの表示） |
| フッター | データの出典と版、数値の出どころ |

章の型（どの章も同じ順）:

1. **ゴールのシート**: `ctx-<シート>.png`、その下にシェルフとマークカードの模式図（`.tbl`）とシート単体の描画。その章で作るピルに `.new` と「← これを作る」
2. **このシートのディメンション**: 置く場所と役割の表。置かないディメンションも、置かない理由と一緒に書く（表計算の方向に効くため）
3. **部品の分解図**: `twb-spec.md` の部品の木から、その章に要る範囲を `.tree` で描く。この章で作る計算は `.make` に手順番号、前の章の計算は `.reuse` に章番号を付ける
4. **手順**: 計算 1〜2 本ごとに「目的 → ヒント → 答え（式と用途）→ 確認の値」。最後の手順で「シートを組み、表計算の方向を決める」: 方向のダイアログ（`.dlg`）、新規シートで忘れやすい設定（並べ替え・軸の固定と反転・不透明度・マークの色と枠線・数値の書式）、手順を終えた画面、確認の値の順

書き方:

- 式は TWB の表記のまま載せ、`<` `>` `&` はエスケープする。TWB のコメント行（`//`）は 60 字以内のものだけ `<span class="cm">` で残す
- ヒントは考え方を 1〜3 項目。答えを言い換えただけの項目は書かない
- 用途の箇条書きは「何を表すか」「どこで使うか」「つまずく点」の順
- 計算の値が画面に出ない章（表計算の部品を作る章）では、検算用のテキスト表シートを作らせ、その表で確認させる。検算シートのディメンションと方向は、その章のシートと同じにする
- 前の章で作った表計算を別の方向で使い直す章（同じ計算で「どの範囲で計算するか」が変わる章）では、シートを組む前に、検算シートでその計算の値を確かめる手順を置く。方向の取り違えが最も起きやすい所なので、確認の値を省かない
- 方向のダイアログは `ordering_type` が `Field` の入れ子計算だけを描き、`order` の順に番号を振る。ビューにあって順序に入らないディメンション（Path など）はチェックなしで描く
- 並べ替えを設定したピルには並べ替えのアイコン（テンプレートの凡例と同じ SVG）を付ける
- 新規シートで既定と違う設定（手動の並べ替え、軸の固定・反転、ペインの書式、計算の既定の数値書式）は、`twb-spec.md` のシートと計算の節から漏れなく拾い、手順の中に「忘れると何が変わるか」と一緒に書く
- 並べ替えに使う計算（部品の木の `Sort <フィールド>`）も、その章で作る計算に含める
- 色の割り当て（`twb-spec.md` の「色の割り当て」）は、そのフィールドを初めて Color に置く章の手順に、値と色コードの表で書く
- 章 0 には、データの役割と型の変更（数値の列をディメンションにする、など）と、ピルの集計を既定から変える所（`MIN(t)` など）を書く。シートの章では、その章で初めて要る変更を手順に入れる
- シートを複製させるときは、複製元との違い（足す・外す・差し替えるピル、ラベルの編集、書式）を `twb-spec.md` の両シートの節から漏れなく挙げる
- 方向のダイアログは、ピルごとの入れ子の一覧（`twb-spec.md` の「表計算 `<ピル>`」）どおりに描く。あるピルの一覧にない計算を、そのピルで設定させない。`ordering_type` が `Field` でない入れ子は「既定のまま」とまとめて書く
- 描画は軸を表示した検証用ワークブックのものなので、「手順を終えた画面」の図の説明に「軸を表示して描画したもの（完成版では軸を隠す）」と書く
- 終章には、ダッシュボードのゾーン（`twb-spec.md` の「ダッシュボード」）から、サイズ・並び・固定の高さ・余白・テキストの文言・フィルターカードの種類を拾って書く
- 「手順を終えた画面」はゴールのシートと同じ描画を使う。画像が 2 回埋め込まれるので、手順書は 2MB 前後になる
- 内部の案の名前・作業ファイル名・検証用ワークブックの名前を書かない

### Step 6: 英語版を書く

日本語版の `walkthrough-ja.src.html` を `walkthrough-en.src.html` にコピーし、構造と画像をそのままに本文を訳す。

- `<html lang="en">`、Google Fonts に `IBM+Plex+Sans` を足し、`--font-body` の先頭に `"IBM Plex Sans"` を置く
- UI 語・部品の見出しは [references/ui-terms.md](references/ui-terms.md) の表に従う。表にない UI 語が出たら、英語版 Tableau の表記を確かめて表に足す
- テンプレートの CSS コメント・HTML コメントの日本語も訳すか消す
- 書き終えたら、CJK 文字が残っていないことを確かめる。Git Bash では `LC_ALL=C.UTF-8 grep -nP "[\x{3040}-\x{30ff}\x{4e00}-\x{9fff}\x{ff00}-\x{ffef}]" <src.html>`（`LC_ALL` がないと `-P` が失敗する）

### Step 7: 組み立てて検査し、撮影する

```bash
python ${CLAUDE_SKILL_DIR}/scripts/build_walkthrough.py --theme-dir outputs/{theme} --lang ja
python ${CLAUDE_SKILL_DIR}/scripts/build_walkthrough.py --theme-dir outputs/{theme} --lang en
```

- `embed:<path>` を data URI に置き換え、`guide/walkthrough-{lang}.html` に書き出す。`--out` で書き出し先を変えられる（試作は `tmp/` へ）
- 個人パス・メールアドレス・Cloud の URL、テーマフォルダ内のすべての `publish-result*.json` のサイト名・プロジェクト名・ワークブック ID が残っていると `ERROR` を出して書き出さない。`YYYYWNN` で始まるワークブック名は出題の公開名なので検査しない
- `WARN` は作業フォルダへの言及。読者は開けないので消す

撮影して、崩れ・はみ出し・空の `{{` を確かめる。

```bash
python ${CLAUDE_SKILL_DIR}/scripts/shoot.py outputs/{theme}/guide/walkthrough-ja.html --out-dir outputs/{theme}/tmp/walkthrough/shots
```

- 1100px 幅と 375px 幅（iframe に入れて撮る。ヘッドレス Chrome は窓幅を 500px 未満にできないため）を撮り、1800px ごとに切った画像を出す
- 切った画像を Read で順に見る。375px 幅では、ページ全体の横スクロールが出ないこと（式の枠と表の中だけが横に流れるのは想定どおり）を見る

ユーザーには、開くコマンドを単独のコードブロックで渡し、見てほしい点を 1 行添える（CLAUDE.md「ユーザーに開いてもらうもの」）。

### Step 8: Pages に載せる

リポジトリ直下の `index.html` の一覧の先頭（`<!-- Add each new challenge ... -->` の直後）に、出題のカードを 1 枚足す。既存のカードの構造（週・題名・日本語と英語のサブブロック）をそのまま写し、リンク先は `outputs/{theme}/guide/walkthrough-ja.html`・`-en.html` にする。

- 公開 URL は `https://<owner>.github.io/<repo>/outputs/{theme}/guide/walkthrough-{ja,en}.html`。出題フォルダ名を変えると URL も変わるので、フォルダ名の確定後に載せる
- 要件の Hints に手順書の URL を載せるかは、出題者に確かめる（`create-requirements` 側の判断）
- `discussion.md` に、手順書を作ったこと・章立て・公開先を追記する

## 参照

- テンプレートと部品: [assets/walkthrough-template.html](assets/walkthrough-template.html)
- 英語版の UI 語: [references/ui-terms.md](references/ui-terms.md)
- 抽出項目の詳細: [scripts/extract_twb.py](scripts/extract_twb.py) の docstring
