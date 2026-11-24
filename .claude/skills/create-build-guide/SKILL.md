---
name: create-build-guide
description: 完成したWOWのTableauワークブックから、作り方を図解する1ファイル完結のHTML(guide/build-guide.html)を作る。TWBから計算式・シェルフ・マークカード・並べ替え・入れ子の表計算の設定を抜き出し、Cloudの描画PNGを埋め込み、データ→計算フィールド→シート→表計算→ダッシュボードの順に解説する。「作り方の解説を作って」「ビルドガイドを作って」「解答のヒントをまとめて」「どう作ったか図解して」「表計算の設定を説明するページ」で使用。要件文やIntroの作成には使わない(create-requirements)。
---

# ビルドガイド作成スキル

完成したワークブックの「どう作ったか」を、出題者が最後に出すヒントとして 1 枚の HTML にまとめる。HTML は `outputs/{theme}/guide/build-guide.html` に置き、リポジトリで管理する。

## 規範

- **事実は TWB と集計から取る**: 式・シェルフ・設定・色・配置の数値は `extract_twb.py` の出力から転記する。描画から推測しない。手で作った説明（用途・理由）だけが Claude の文章になる
- **数値は再計算してから載せる**: 金額・割合・位置などは Step 4 の照合スクリプトで出した値だけを書く。照合できない数値は載せない
- **明るい配色に固定する**: Tableau の描画が白背景のため。`assets/guide-template.html` の CSS とトークンをそのまま使い、ダークモード対応を足さない
- **余白を削らない**: 1 つの部品に詰め込まない。計算フィールドは 1 列に並べ、説明の箇条書きは 2〜3 項目に抑える
- **Public 化前提**: 実プロジェクト名・Cloud のサイト名・URL・個人パス・メールアドレス・作業フォルダのパスを書かない。`build_guide.py` が検出して書き出しを止める
- **根拠のない説明を書かない**: 「こうすると〜になる」という説明は、TWB・照合スクリプト・描画のどれかで確かめたものだけ書く。確かめていない一般論や推論は削る
- **文体**: 日本語は CLAUDE.md の個人ルール（一文一義、結論先行）に従う。フィールド名・シート名・メニュー名は Tableau の英語表記のまま書く

## 入力と出力

| 種類 | パス（`outputs/{theme}/` から） |
|---|---|
| 入力: ワークブック | 最終 publish した `.twbx`（`refine/publish-result.json` の `source`）。Cloud で直された場合は `analyze-twbx` の Cloud 経路で pull した TWB |
| 入力: 完成図 | `refine/render/guide/<label>.png`（Step 2 で作る） |
| 中間: 抽出結果 | `tmp/guide/twb-spec.json`・`tmp/guide/twb-spec.md` |
| 中間: 照合スクリプト | `tmp/guide/check_numbers.py` |
| 中間: HTML ソース | `tmp/guide/build-guide.src.html`（画像は `embed:` 参照のまま） |
| 出力 | `guide/build-guide.html`（画像は data URI で埋め込み済み、1 ファイル完結） |

パイプライン上は `create-workbook` の refine ループが終わった後に使う。`create-requirements`（確定）の前でも後でもよい。

## 依存

- Python 3.10+、`tableauserverclient`・`python-dotenv`（`publish-to-cloud` と同じ。`pip install -r .claude/skills/publish-to-cloud/scripts/requirements.txt`）
- 照合スクリプトで Excel を読むなら `pandas`・`openpyxl`

## 手順

```
進捗:
- [ ] Step 1: TWB を抽出する
- [ ] Step 2: 完成図を状態ごとに描画する
- [ ] Step 3: 解説の骨子を決める
- [ ] Step 4: 数値を照合する
- [ ] Step 5: HTML ソースを書く
- [ ] Step 6: 組み立てて検査する
- [ ] Step 7: 見た目を確かめ、ユーザーに渡す
```

### Step 1: TWB を抽出する

```bash
python ${CLAUDE_SKILL_DIR}/scripts/extract_twb.py outputs/{theme}/refine/<final>.twbx --json outputs/{theme}/tmp/guide/twb-spec.json --md outputs/{theme}/tmp/guide/twb-spec.md
```

`twb-spec.md` を読む。JSON は部品を組むときに必要な項目だけ引く。抽出される内容:

- `counts`: シート・計算フィールド・表計算（自分で表計算関数を使うもの）・LOD の数。ヘッダーの数字はここから取る
- 計算フィールドの `kind`: `row`（行レベル）/ `agg`（集計）/ `tc`（表計算）/ `tc-derived`（表計算を参照するだけ）/ `lod`
- シートごとの Rows・Columns のピル（連続/不連続、表計算か）、マークカードの並び、入れ子の表計算の `ordering_type` と `order`、手動の並べ替え、保存時のフィルター値、軸の固定、不透明度、ラベルの編集
- 色の割り当て、ダッシュボードの各ゾーンの位置と幅（ダッシュボード全体に対する %）

publish 済みの `.twbx` と手元の作業ファイルが違うことがある。`refine/publish-result.json` の `source` と同じファイルを読む。

### Step 2: 完成図を状態ごとに描画する

フィルターの状態ごとに Cloud で描画する。状態は 2 つが目安で、Viz の振る舞いが変わる組み合わせ（正負が入れ替わる、片側が空になる等）を 1 つ含める。

```bash
python ${CLAUDE_SKILL_DIR}/scripts/render_states.py --theme-dir outputs/{theme} --view <Dashboard> \
  --state "all|Region=Central,East,South,West" --state "<label>|Region=South"
```

- 出力は `refine/render/guide/<label>.png` と `states.json`
- フィルターのない状態のラベルは `all` にする（テンプレートの既定）
- フィルターを付けない `--state "<label>"` は、ワークブックに保存された状態で描画する。保存時にフィルターがかかっている場合（Step 1 の「保存時の値」）、「フィルターなし」は全値を列挙して指定する
- 描画した PNG は Read で開き、状態が意図どおりか確かめる

### Step 3: 解説の骨子を決める

`twb-spec.md` と描画を見て、次を決める。HTML を書く前にここで決めきる。

1. 計算フィールドのまとまり（A, B, C …）と並び順。依存の上流から下流へ並べ、1 まとまりは 2〜6 本
2. 核となる計算を 1 つ選ぶ。普通の作り方（参考ワークブックや定番の手法）にない計算で、Viz の要点を担うもの。これに「なぜ要るのか」の囲みを付ける。囲みは核の計算のカードの直後に置き、同じまとまりの残りのカードは囲みの後に続ける（まとまりを割らない）
3. STEP 4 で図にする表計算: `ordering_type` が `Field` の入れ子計算だけをダイアログにする。複数シートで同じ設定は 1 つにまとめ、Viz に固有の設定に `hl` を付ける
4. STEP 3 のシートの順: ダッシュボードの配置順（左→右、上→下）。抽出結果の順ではない
5. 載せる数値の一覧（完成図の説明、囲みの計算例、位置の表など）

### Step 4: 数値を照合する

載せる数値は、元データから再計算するスクリプトを `tmp/guide/check_numbers.py` に書いて出す。

- データは `.twbx` に同梱されたファイル（`twb-spec.md` の「同梱ファイル」）を zip から直接読む
- 計算は TWB の式をそのまま Python に移す。表計算は、Step 1 の `order` の順で並べてから累積・合計する。各ディメンションの中の順は、そのシートに手動の並べ替えがあればその順、なければ昇順（アルファベット順）
- フィルターの状態ごとに、Step 2 と同じ条件で絞って出す
- 出力と描画（ラベルの金額、帯や棒の位置）を突き合わせる。合わなければ、式の写し間違いか、描画の状態違いかを確かめてから先に進む
- HTML には、このスクリプトの出力と一致した値だけを書く。0〜1 の割合は小数 3 桁、金額は整数ドルに丸め、表の中で桁を揃える
- Windows では先頭で `sys.stdout.reconfigure(encoding="utf-8")` を呼ぶ。`–` や `→` を含む出力が cp932 で落ちるため

### Step 5: HTML ソースを書く

`assets/guide-template.html` を `tmp/guide/build-guide.src.html` にコピーし、`{{...}}` を埋める。構成は固定する（必ずこの順、この部品）:

| 節 | 内容 | 主な出どころ |
|---|---|---|
| ヘッダー | 題名、2〜3 文の要旨、数のバッジ | `counts` |
| 完成図 | 状態の切り替えボタン、描画、状態ごとの説明 | Step 2・Step 4 |
| STEP 1 データ | 表の結び方、補助テーブルの中身、つまずく設定 | データソース・リレーションシップ |
| STEP 2 計算フィールド | まとまりごとに、式（左）と用途の箇条書き（右）を 1 列に並べる。核の計算の直後に「なぜ要るのか」の囲み | 計算フィールド・Step 3 |
| STEP 3 シート | シートごとにマークカードとシェルフの模式図、その下に設定の箇条書き | シート |
| STEP 4 表計算 | 入れ子の計算ごとの設定ダイアログの模式図、積んだ結果の表 | 表計算・Step 4 |
| STEP 5 ダッシュボード | ゾーンの配置図（幅は抽出値の %）、フィルターの適用先、色の割り当て | ダッシュボード・色 |
| フッター | データの出典と版、参考ワークブックの一般名、描画日 | — |

書き方:

- 式は TWB の表記のまま載せ、`<` `>` `&` はエスケープする。TWB のコメント行（`//`）は 60 字以内のものだけ `<span class="cm">` で残し、長いものは削って内容を用途の箇条書きに回す（枠からはみ出して読めないため）
- 用途の箇条書きは「何を表すか」「どこで使うか」「つまずく点」の順。式を言い換えるだけの項目は書かない
- 「なぜ要るのか」の囲みは、普通の作り方で起きる問題 → この計算の解き方 → 状態ごとの計算例（`ratio-card`）→ 式の性質、の順
- シートの模式図のピルは、抽出結果の連続/不連続と △ に従う。マークカードはカード上の並び順にする
- 複数シートで同じ設定をまとめたダイアログは、見出しを `表計算 – <シート名> / <シート名>` にする
- フィルターの適用先は `twb-spec.md` の「共有フィルター」から書く
- ダイアログは `order` の順に番号を振り、ビューにあって `order` に含まれないディメンション（Path 等）はチェックなしで描く
- 説明に内部の案の名前（A 案・B 案など）や作業ファイル名を書かない

### Step 6: 組み立てて検査する

```bash
python ${CLAUDE_SKILL_DIR}/scripts/build_guide.py --theme-dir outputs/{theme}
```

- `embed:<path>` を data URI に置き換え、`guide/build-guide.html` に書き出す
- 個人パス・メールアドレス・Cloud の URL・`publish-result.json` のサイト名/プロジェクト名/ワークブック ID が残っていると `ERROR` を出して書き出さない。ソースから消して再実行する
- `WARN` は作業フォルダへの言及。読者は開けないので、原則として消す

### Step 7: 見た目を確かめ、ユーザーに渡す

ヘッドレス Chrome で全体を撮り、Read で確認する。崩れ・はみ出し・空の `{{` が残っていないかを見る。

```bash
"<chrome>" --headless=new --disable-gpu --hide-scrollbars --window-size=1100,14000 --screenshot=outputs/{theme}/tmp/guide/shot.png outputs/{theme}/guide/build-guide.html
```

- `<chrome>` は Windows なら `C:/Program Files/Google/Chrome/Application/chrome.exe`、macOS なら `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- パスは絶対パスで渡す。相対パスだと Chrome が URL として解釈する
- 縦の長さはページより長くする（目安 14000）。足りないと下が切れる
- スマホ幅も確かめる。ヘッドレス Chrome は窓幅を 500px 未満にできないので、`tmp/guide/frame.html` に `<iframe src="../../guide/build-guide.html" style="width:375px;height:3000px">` を置き、それを撮る。ページ全体の横スクロールが出ないこと（式の枠の中だけが横に流れるのは想定どおり）を見る

ユーザーには、開くコマンドを単独のコードブロックで渡し、見てほしい点を 1 行添える（CLAUDE.md「ユーザーに開いてもらうもの」）:

```bash
start outputs/{theme}/guide/build-guide.html
```

## 参照

- 部品の HTML と CSS: [assets/guide-template.html](assets/guide-template.html)
- 抽出項目の詳細: [scripts/extract_twb.py](scripts/extract_twb.py) の docstring
