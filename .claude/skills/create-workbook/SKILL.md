---
name: create-workbook
description: 要件文を元にTableauワークブック(.twbx)を生成する。テンプレTWBXをベースに、計算フィールド・パラメータ・複数シート・ダッシュボード・デュアル軸を差分編集で組み立てる。「ワークブックを作って」「TWBXを生成」「Tableau Desktopで開ける状態で出して」で使用。Sankey等の特殊チャートは対象外。
---

# Tableauワークブック生成スキル

要件文（`requirements-en.md`）とプロトタイプ（任意 `prototype/*.html`）を入力に、`common/WOW Challenge Template (Save a copy) .twbx` をベースに `.twbx` を組み立てる。

## 設計の原則

**2 段階で組み立てる**:
1. **足場はパッチ JSON で作る**: テンプレの展開と、計算フィールドの一括投入（フォルダ分け込み）は `apply-edits.ts` が決定論的に行う。式の XML エスケープと改行の変換を任せられる
2. **シートとダッシュボードは `refine/wb-build/` の TWB を直接編集して作る**: パラメータ、Pivot、色の割り当て、横並びや固定高さのダッシュボードはパッチで表せない。足場ができたら、以後は TWB を直接編集する。直接編集とは、Claude が TWB の XML ファイルを書き換えること。Tableau Desktop での操作ではない

テンプレ由来の `<workbook>` ルート、データソース接続、フォントは温存する。

直接編集で XML を書くときの参照先:
- 骨格: [references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md)
- 構文の置き場所と属性: [scripts/vendor/tableau-plugin/resources/examples/](scripts/vendor/tableau-plugin/resources/examples/) の同名 JSON（XML を抽象化した表記。属性名は XSD 検証で確かめる）と、版に合う XSD（[scripts/vendor/tableau-plugin/resources/schemas/](scripts/vendor/tableau-plugin/resources/schemas/)）
- Desktop で失敗する書き方: [references/twb-pitfalls.md](references/twb-pitfalls.md)

### 参加者が再現できる規模にする

WOW の解答は人間が作り直すもの。動くだけでなく、熟練の Tableau 作者が自然に選ぶ作り方にする。

- 計算フィールドの本数は構造を疑う合図であって、削る基準ではない。目安（答え 1 つに 5 前後、全体で 25 以内。出題の規模で前後する）を超えたら、フィールドを削る前に構造を疑う
- 平均線と「平均 ± n SD」の帯はアナリティクスペイン相当の参照線で描き、フィールドにしない（書き方は [references/twb-pitfalls.md](references/twb-pitfalls.md) の「マークとシェルフ」）
- 指標が複数あるときは、データソースで Pivot して 1 組の計算でまかなう。Measure Names は計算式で参照できず、パラメータ切替は同時表示できない
- 文字列の色分けは 1 色 1 フィールドかかる。記号（✓ ✕ ⚠）で代替できないか先に検討する
- 各式の先頭に `//` で「なぜ」を 1 行書く。定数（13 週など）は要件で固定ならパラメータにせず、コメントで意味を書く
- 命名は「指標・比較軸 → 統計量」の順（例：`Usual Avg` / `Last Year SD`）にし、同種のフィールドが並ぶようにする。フォルダは番号付き
- 判定は boolean、3 値以上の状態だけ文字列にする
- 計算はすべてデータソース（`<datasources>`）に定義する。`MIN(1.0)` のような 1 行の補助式も同じ。ワークシートの `<datasource-dependencies>` にだけ書いても、Tableau はデータペインに計算フィールドとして出す。そのうえ定義がシートごとに重複し、片方だけ直すとずれる

要素（表示・シート・計算フィールド）を残すか消すかは、次の 3 問で決める。本数を減らすこと自体は目的にしない。

1. 同じ情報が、他の要素から一目で読めるか。読めるなら、その表示と、それだけのために作ったシート・計算を消す（例：範囲外のタイルが濃く塗られているのに、範囲外の件数を別に出す）
2. 同じ条件・比較を 2 か所以上に書いていないか。書いているなら、既存フィールドの参照に書き換える（例：状態フィールドがあるのに、答えのフィールドで同じ比較をやり直す）
3. 消す・まとめると、参加者の手順が増えるか、式が読みにくくなるか。そうなるなら残す（例：数値書式を分けるための差額フィールド、`Usual` と `Last Year` の対）

式の型は [references/calc-field-patterns.md](references/calc-field-patterns.md)（ネスト LOD の平均・SD、行ごとの文字列の連結）を使う。

見た目の課題（色付きタイル、強調点、ラベルの重なり、目標・前年との比較など）は、計算や工程を足す前に [references/viz-techniques.md](references/viz-techniques.md) の定石から選ぶ。少ない手順で済み、参加者にも馴染みのある作り方になる。色・強弱・見せ場の決め方は [references/dashboard-design.md](references/dashboard-design.md) に従う。

## 標準手順

### Step 1: 前提確認
- `outputs/{theme}/requirements-en.md` を読む
- `outputs/{theme}/prototype/*.html` があれば参照（Vizイメージの認識合わせ）
- 要件が指定するデータと期間を確認する。テンプレの抽出は古い時点のデータなので、通常は `common/` の Excel に差し替える（Step 4）。列の構成がテンプレと違うデータは対象外（[制約・対象外](#制約対象外) 参照）

### Step 2: スキーマ更新確認（任意）
新Tableau機能を試したい時など、最新XSDが必要そうなら:

```bash
npx tsx .claude/skills/create-workbook/scripts/check-schema-updates.ts
```

24時間キャッシュあり。更新があればリリースノートを表示し、ユーザー判断で `update-schemas.ts` 実行。

### Step 3: パッチJSONの起案
要件から計算フィールドの一覧を抽出し、`outputs/{theme}/tmp/workbook-patch.json` に書き出す（フォーマットは [パッチJSON仕様](#パッチJSON仕様) 参照）。

起案前に [references/twb-pitfalls.md](references/twb-pitfalls.md) を読み、文字列の引用符・数値書式・計算フィールドのフォルダ分けを規範どおりにする。式の中で別の計算フィールドを指すときは、キャプションではなく内部名で書く。内部名はパッチの並び順に `[Calculation_001]` から振られるので、参照される側を先に並べ、順番から内部名を決める。パラメータは `[Parameters].[Parameter 1]` の形で指す。

書き出したらユーザーにレビューしてもらう。

### Step 4: 足場の生成 → 直接編集 → 検証

```bash
SKILL=".claude/skills/create-workbook"
THEME_DIR="outputs/2026-MM-DD-theme"
PATCH="$THEME_DIR/tmp/workbook-patch.json"

# 1. テンプレTWBXを作業ディレクトリ (refine/wb-build) に展開
npx tsx $SKILL/scripts/unpack-template.ts --patch "$PATCH"

# 2. パッチをTWB XMLに適用 (出力の calcIdMap がキャプション → 内部名の対応表)
npx tsx $SKILL/scripts/apply-edits.ts --patch "$PATCH"
```

`unpack-template.ts` は `refine/wb-build/` を消してから展開し直す。直接編集を始めた後に再実行すると、その編集はすべて失われる。計算フィールドを後から足すときは、パッチに戻らず TWB に直接足す。

続けて `refine/wb-build/*.twb` を直接編集する:

1. テンプレの残り物を消す。`<worksheet name='Sheet 1'>`、`<dashboard name='Goal'>`（過去の出題の画像を載せたもの）と、それぞれの `<window>` を削除する
2. データソースを出題のデータに差し替える（[references/twb-pitfalls.md](references/twb-pitfalls.md) の「データソースの差し替え」）。Pivot が要るなら、その後で relation を書き換える（同「データソースの Pivot」）
3. パラメータが要るなら `Parameters` データソースを足す（現行テンプレには無い。書き方は cheatsheet の「パラメータ」）
4. シート、ダッシュボード、`<window>` を書く。XML 内で計算フィールドを指すときは、キャプションではなく `calcIdMap` の内部名（`[Calculation_001]`）を使う

編集したら検証して `.twbx` にまとめる:

```bash
# 3. 検証 (XML well-formed + 必須要素 + キャプション重複)
npx tsx $SKILL/scripts/validate-twb.ts --patch "$PATCH"

# 4. XSD検証 (source-build に合う版の公式XSDを自動選択。要 lxml)
python $SKILL/scripts/vendor/tableau-plugin/scripts/validate_workbook.py "$THEME_DIR/refine/wb-build/<テンプレ由来の名前>.twb"

# 5. TWBX (ZIP) に再パッケージ
npx tsx $SKILL/scripts/repack-twbx.ts --patch "$PATCH"
```

検証で失敗したら、エラーメッセージを元に TWB を直して再実行する。

XSD検証の結果は「構造が正しい」までで、Desktop で開けることは保証しない：
- 計算式・フィールド参照・データソース接続は検証対象外
- XSD を通っても Desktop が拒否する属性があり、逆に XSD が要求しても Desktop が拒否する要素もある。無視してよい XSD エラーは [references/twb-pitfalls.md](references/twb-pitfalls.md) に載っている食い違いだけ。それ以外のエラーが 3 回直しても残るときは、ユーザーに報告して止まる
- 構文が分からない要素は推測で書かず、Desktop で同じ操作をして `.twb` に別名保存し、その XML を写す。GitHub のコード検索で見つからないとき（例：動的パラメータ）は、ユーザーに 1 回作って保存してもらうのが速い

### Step 5: refine ループで表示を詰める

Desktop は開いているワークブックを XML から再読込できないので、表示の試行錯誤は Cloud を描画エンジンにして回す。作業は `outputs/{theme}/refine/`（gitignore 済み）で行う。Cloud 認証は publish-to-cloud Skill の前提に従う。

```
outputs/{theme}/
  prototype/*.html        ドラフト HTML（create-requirements が作る。gitignore 済み）
  refine/
    YYYYWNN.twbx          作業用かつ publish 対象。テーマ直下には .twbx を置かない
    refine.html           refine 中に改訂するドラフト HTML。1 ファイルを上書きで育てる（prototype/ があればコピーして始め、無ければ新規に作る）
    wb-build/             編集中の TWB（初回に .twbx から展開）
    compare.html          比較ページ（assets/compare.html のコピー。ファイルのまま開く）
    compare-data.js       比較ページが読むドラフト一覧と描画の一覧（iterate.ts が毎回書き直す）
    render/*.png          Cloud の描画
    publish-result.json   publish 結果
    backup/               上書き前の Cloud 版
    HANDOFF.md            合意した変更の経緯（ドラフトのメモ欄から移す）
```

1 ラウンドは次の 1 コマンドで回す:

```bash
npx tsx $SKILL/scripts/iterate.ts --twbx "$THEME_DIR/refine/2026W40.twbx" [--views "Dashboard"] [--patch "$PATCH"]
```

`iterate.ts` は、TWB の整形式チェック → `.twbx` への再梱包 → `publish.py --overwrite --render` を順に行う。`--patch` を付けると `validate-twb.ts`（必須要素・シートごとの `<window>`・キャプション重複）も走る。XSD 検証は含まないので、Step 4 の XSD 検証を通した後に始める。

`iterate.ts` は `wb-build/` があればそれを正とし、毎回そこから `.twbx` を作り直す。`wb-build/` が無いときだけ `.twbx` を展開する。手作業で作った `.twbx` や Cloud から取得した版から始めるときは、それを `refine/YYYYWNN.twbx` に置き、古い `wb-build/` はユーザーに消してもらってから実行する。

比較ページは `refine/compare.html` をブラウザでファイルのまま開く（サーバー不要）。左にドラフト HTML（`refine/` と `prototype/` の両方から選べる）、右に Cloud の描画 PNG が並ぶ。

- 一覧は `iterate.ts` が書き出す `compare-data.js` から読む。「Reload both」はこのファイルとドラフト・PNG を読み直す
- ドラフト HTML を足しただけで publish しないときは、`iterate.ts --twbx ... --compare-only` で一覧だけ更新する
- ユーザーと画面を見ながら進めるときは、このページを Chrome で開いて共有する。Claude in Chrome で読むには次の 2 つが要る
  - 拡張機能の詳細で「ファイルの URL へのアクセスを許可する」をオンにする。切り替えると拡張機能が再読み込みされ、既存のタブグループは Claude から見えなくなるので、タブグループは作り直す
  - `navigate` は `file://` を `https://` に書き換えるため使えない。Claude のタブグループに空タブを作り、ユーザーにそのアドレスバーへ file URL を貼ってもらう。以後の読み取り（`get_page_text`・`javascript_tool`・スクリーンショット）は動く
- Claude Code デスクトップの組み込みブラウザは `file://` を静的スナップショットにするため、`compare-data.js` を読めず空になる。使わない

見せ方の変更（レイアウト・文言・情報の削減）は、TWB より先にドラフト HTML で合意する。HTML は数秒で直せ、publish の待ちがない。`prototype/` の原案は要件段階の記録として残し、改訂は `refine/refine.html` を上書きする。版番号は付けない。HTML では Tableau で再現できる表現だけを使う。高さ不足の `#####` や空白の追加のような機械的な修正は、HTML を挟まず TWB を直す。

ドラフトの横のメモ欄には、いま議論している論点だけを置く（案の切り替え、決めてほしいこと、Tableau での実装の見込み）。合意した変更はドラフト本体に反映してメモから消し、経緯は `refine/HANDOFF.md` に残す。変更点を積み上げると、どこを見てほしいのかが埋もれる。

ループの回し方:

1. `refine/wb-build/*.twb` を直接編集する
2. `iterate.ts` を実行する
3. `renders[].png` を Read し、要件・ドラフト HTML と比べて差分を列挙する。観点は「空白ゾーン」「期待値との一致」「色・線・折り返し」「`#####` 表示」
4. 差分があれば 1 に戻る。空白シートや `#####` の原因は [references/twb-pitfalls.md](references/twb-pitfalls.md) で当たる

PNG は静止画なので、ツールヒント・パラメータ・ハイライト動作は `webpageUrl` をブラウザで開いて確かめる。

Cloud 側の画像キャッシュで前回の絵が返ることがある（1 分未満の連続 publish）。変化が見えないときは 1 分待って `iterate.ts` を再実行する。

描画がドラフトと一致したら、ループを抜ける前に次の 2 つを済ませる。ここで TWB を直したら、ループの 1 に戻る。

1. **値の検算**: 要件 1 行につき描画上の値を 1〜2 個選び、出題データの Excel から独立に集計して一致を確かめる（pandas など）。少なくとも、既定のパラメータ値での判定（Yes / No・範囲外）、件数、最大・最小は当てる
2. **簡素化レビュー**: 使用表を出し、`fieldUsage` の 1 行ごとに「参加者が再現できる規模にする」の 3 問を当てる

   ```bash
   npx tsx .claude/skills/analyze-twbx/scripts/twbx/structure.ts "$THEME_DIR/refine/wb-build/<名前>.twb" --usage
   ```

   - `unused: true` のフィールドと、`sheetsNotOnDashboard` のシートは外す
   - `kind: sheet-local` の計算は、データソースに移す
   - `usedIn` が `lod` や `tooltip` だけのフィールドは、参照線（`reference-line`）やツールヒント本文（`tooltip-text`）で使われていなければ外す
   - 名前とコメントが、いまの用途（`usedIn` の棚）と合っているかを見る
   - 描画を見て、他の要素と同じ情報を繰り返している表示を探す。ドラフト HTML の段階では見えなかった重複がここで見える
   - 表示を消したら、ドラフト HTML（`refine/refine.html`）も合わせて直す

### Step 6: 要件文の照合と Desktop での最終確認

Desktop で開く前に、`requirements-{ja,en}.md` を 1 行ずつ現物と照らす。refine ループで要素を消したり変えたりした分が、要件文に残りやすい。キーワード検索だけでは、言い回しの違う行を見落とす。英語版は本文と HTML 埋め込みの両方を直す。


Cloud で表示が固まったら `.twbx` を Tableau Desktop で開いて確認する。Cloud では通るが Desktop が拒否する属性があるため、この確認は省かない。

- 開き直しはユーザーに頼む（Desktop で開いている版は再生成しても更新されない。保存せずに閉じてから開き直す）
- Desktop で `refine/YYYYWNN.twbx` に上書き保存しない。`iterate.ts` は毎回 `wb-build` の TWB から作り直すので、その変更は次のラウンドで消える。Desktop での変更は `tmp/` に別名で保存し、XML を写して `wb-build` に反映する
- Computer Use で Desktop を操作すると、Windows の入力パネル（`textinputhost.exe`）が前面を奪い、クリックがすべて拒否されることがある。数十秒で済む単発の操作（書式を 1 つ変えて別名保存する等）はユーザーに頼む
- 問題なければ Step 5 の最後の publish が公開版になる。`refine/publish-result.json` の `webpageUrl` を次の `create-x-post` が読む

## パッチJSON仕様

```json
{
  "baseTemplate": "common/WOW Challenge Template (Save a copy) .twbx",
  "outputPath": "outputs/{theme}/refine/2026W40.twbx",
  "workingDir": "outputs/{theme}/refine/wb-build",
  "calculatedFields": [
    {
      "caption": "Profit Ratio",
      "datatype": "real",
      "role": "measure",
      "type": "quantitative",
      "formula": "SUM([Profit])/SUM([Sales])",
      "defaultFormat": "*+0.0%;-0.0%;0.0%",
      "folder": "2_Stats"
    }
  ]
}
```

- `calculatedFields[].formula` には改行と `//` コメントを書いてよい（TWB では `&#13;&#10;` に変換される）
- `calculatedFields[].folder` を指定すると、データペインのそのフォルダに入る（`<folders-common>` に追記。同名フォルダがあれば合流）。フォルダの切り方は [references/twb-pitfalls.md](references/twb-pitfalls.md) の「計算フィールドの整理」に従う
- `calculatedFields[].defaultFormat` は既定の数値書式（省略可）。動作確認済みの書式は twb-pitfalls.md の「数値書式」
- `calculatedFields[].datasource` は省略する。省略すると、テンプレの主データソース（`Parameters` 以外で最初のもの）に入る
- 内部名は `[Calculation_001]` からパッチの並び順に振られる。式の中の計算フィールド参照はこの内部名で書く（`apply-edits.ts` はキャプションを内部名に置き換えない）
- `worksheets[]`（`name` と `rawXml`）と `dashboards[]`（`name`・`size`・`sheets`）も書けるが、ダッシュボードは全シートを縦に等分するだけになる。通常は使わず、直接編集で書く
- `outputPath` は `outputs/{theme}/refine/YYYYWNN.twbx`（WOW の週番号を 2 桁ゼロ埋め）。Cloud 上のワークブック名はこのファイル名から決まる
- `workingDir` を省略すると `refine/wb-build` を使う（`iterate.ts` と同じ場所）

## 参照ファイル

- [references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md) — TWB XML骨格チートシート
- [references/calc-field-patterns.md](references/calc-field-patterns.md) — 計算フィールド/LOD/パラメータの実例XML
- [references/twb-pitfalls.md](references/twb-pitfalls.md) — XSDを通ってもDesktopで失敗・表示崩れする原因と回避規範（引用符・書式・色・線・テキスト・レイアウト・フォルダ分け）
- [references/dashboard-design.md](references/dashboard-design.md) — 色（明るさの 3 段、色は意味にだけ）・見せ場・線の強弱・出題の既定値の選び方と、案を HTML で比べて決める進め方
- [references/viz-techniques.md](references/viz-techniques.md) — 少ない手順で見た目が良くなる定石（`MIN(1.0)` タイル、二重軸の強調点、別メジャーの参照帯、ラベル設定など）と実証済みの XML
- `references/schemas/` — Tableau公式XSDの最新スナップショットを置く手元キャッシュ（gitignore対象。新機能の構文を読むときに `update-schemas.ts` で取得）
- [assets/compare.html](assets/compare.html) — refine ループの比較ページのひな形（`iterate.ts` が `refine/` にコピーし、テンプレートが変われば上書きする）
- [scripts/vendor/tableau-plugin/](scripts/vendor/tableau-plugin/) — `tableau/tableau-plugin` から取り込んだXSD検証スクリプト・版別XSD（2025.1〜2026.2）・構文例JSON（Apache-2.0。出典は `SOURCE.md`）

## 初回セットアップ

```bash
cd .claude/skills/create-workbook/scripts && npm install
pip install -r vendor/tableau-plugin/scripts/requirements.txt   # XSD検証用の lxml
```

## 制約・対象外

- **対象外**: Sankey, Radial, Hex Tile, Map, Web Data Connector
- データの差し替えは、列の構成がテンプレと同じ Excel（`common/Sample - Superstore.xlsx`）に限る。列の構成が違うデータは未対応
- パラメータはパッチで表せない。TWB の直接編集で足す（[references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md) の「パラメータ」）
- XSD検証は 2025.1 より古い `source-build` のブックを検証できない
- Tableau Desktop自動検証CLIは存在しない。描画の自動確認は Cloud 経由（Step 5）で行い、Desktop での最終確認は手動（Step 6）
