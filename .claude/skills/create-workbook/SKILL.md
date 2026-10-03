---
name: create-workbook
description: 要件文を元にTableauワークブック(.twbx)を生成する。テンプレTWBXをベースに、計算フィールド・パラメータ・複数シート・ダッシュボード・デュアル軸を差分編集で組み立てる。「ワークブックを作って」「TWBXを生成」「Tableau Desktopで開ける状態で出して」で使用。Sankey等の特殊チャートは対象外。
---

# Tableauワークブック生成スキル

要件文（`requirements-en.md`）とプロトタイプ（任意 `prototype/*.html`）を入力に、`common/WOW Challenge Template (Save a copy) .twbx` をベースに差分編集で `.twbx` を生成する。

## 設計の原則

**ハイブリッド戦略**（3層）:
1. **テンプレ流用**: `<workbook>` ルート、データソース、フォント等はテンプレ由来を温存
2. **レシピ挿入**: 計算フィールド、パラメータ、参照線、デュアル軸など定型は [references/chart-recipes/](references/chart-recipes/) のXMLテンプレを差し替え挿入
3. **局所スキーマ駆動**: 新規ワークシート全体は [references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md) と、版に合うXSD（[scripts/vendor/tableau-plugin/resources/schemas/](scripts/vendor/tableau-plugin/resources/schemas/)）を参照してXMLを書く。参照線・デュアル軸・パラメータ・LOD・フィルタ・ダッシュボードなどの構文は、書く前に [scripts/vendor/tableau-plugin/resources/examples/](scripts/vendor/tableau-plugin/resources/examples/) の同名 JSON で要素の置き場所と属性を確認する（JSON は XML を抽象化した表記。属性名は XSD 検証で確かめる）

**ClaudeにTWB XMLを直書きさせず、パッチJSONを介する**。`apply-edits.ts` がパッチを決定論的にXMLに反映する。

### 参加者が再現できる規模にする

WOW の解答は人間が作り直すもの。動くだけでなく、熟練の Tableau 作者が自然に選ぶ作り方にする。

- 計算フィールドは 1 判定あたり 5 前後、全体で 25 以内を目安にする。超えたらフィールドを削る前に構造を疑う
- 平均線と「平均 ± n SD」の帯はアナリティクスペイン相当の参照線で描き、フィールドにしない。除外したいマーク（今週など）は別ペインに分ける
- 指標が複数あるときは、データソースで Pivot して 1 組の計算でまかなう。Measure Names は計算式で参照できず、パラメータ切替は同時表示できない
- 文字列の色分けは 1 色 1 フィールドかかる。記号（✓ ✕ ⚠）で代替できないか先に検討する
- 各式の先頭に `//` で「なぜ」を 1 行書く。定数（13 週など）は要件で固定ならパラメータにせず、コメントで意味を書く
- 命名は「指標・比較軸 → 統計量」の順（例：`Usual Avg` / `Last Year SD`）にし、同種のフィールドが並ぶようにする。フォルダは番号付き
- 判定は boolean、3 値以上の状態だけ文字列にする

式の型は [references/calc-field-patterns.md](references/calc-field-patterns.md)（ネスト LOD の平均・SD、行ごとの文字列の連結）を使う。

## 標準手順

### Step 1: 前提確認
- `outputs/{theme}/requirements-en.md` を読む
- `outputs/{theme}/prototype/*.html` があれば参照（Vizイメージの認識合わせ）
- 出題で **Sample-Superstore以外のデータが必要か** を確認（Phase 2: `python/swap_datasource.py`）

### Step 2: スキーマ更新確認（任意）
新Tableau機能を試したい時など、最新XSDが必要そうなら:

```bash
npx tsx .claude/skills/create-workbook/scripts/check-schema-updates.ts
```

24時間キャッシュあり。更新があればリリースノートを表示し、ユーザー判断で `update-schemas.ts` 実行。

### Step 3: パッチJSONの起案
要件から次を抽出して `outputs/{theme}/tmp/workbook-patch.json` に書き出す（フォーマットは [パッチJSON仕様](#パッチJSON仕様) 参照）:
- 計算フィールド一覧
- パラメータ一覧
- シート構成（recipe名 or rawXml）
- ダッシュボード配置

起案前に [references/twb-pitfalls.md](references/twb-pitfalls.md) を読み、文字列の引用符・数値書式・色の割り当て・計算フィールドのフォルダ分けを規範どおりにする。

書き出したらユーザーにレビューしてもらう。

### Step 4: 適用 → 検証 → 生成

```bash
SKILL=".claude/skills/create-workbook"
THEME_DIR="outputs/2026-MM-DD-theme"
PATCH="$THEME_DIR/tmp/workbook-patch.json"

# 1. テンプレTWBXを作業ディレクトリに展開
npx tsx $SKILL/scripts/unpack-template.ts --patch "$PATCH"

# 2. パッチをTWB XMLに適用
npx tsx $SKILL/scripts/apply-edits.ts --patch "$PATCH"

# 3. 検証 (XML well-formed + 必須要素 + フィールド参照整合性)
npx tsx $SKILL/scripts/validate-twb.ts --patch "$PATCH"

# 3b. XSD検証 (source-build に合う版の公式XSDを自動選択。要 lxml)
python $SKILL/scripts/vendor/tableau-plugin/scripts/validate_workbook.py "$THEME_DIR/refine/wb-build/<name>.twb"

# 4. TWBX (ZIP) に再パッケージ
npx tsx $SKILL/scripts/repack-twbx.ts --patch "$PATCH"
```

Step 3・3b で失敗したら、エラーメッセージを元にパッチJSONを修正し再実行（最大3回ループ）。

XSD検証の結果は「構造が正しい」までで、Desktop で開けることは保証しない：
- 計算式・フィールド参照・データソース接続は検証対象外
- `document-format-change-manifest` の機能フラグに依存する属性（例: パラメータの `period-type-v2`、参照線の `tooltip-type`）は XSD を通っても Desktop で拒否される。新しい属性は、テンプレと同じ `source-build`・同じ manifest を持つ実ブックに現れるものだけを使う
- 逆に XSD が要求しても Desktop が拒否する要素がある（例: 手動ソートは `<manual-sort>` ではなく `<sort class='manual'>`）。Desktop で開けるならその XSD エラーは無視する。既知の食い違いは [references/twb-pitfalls.md](references/twb-pitfalls.md) にある
- 構文が分からない要素は推測で書かず、Desktop で同じ操作をして `.twb` に別名保存し、その XML を写す

### Step 5: refine ループで表示を詰める

Desktop は開いているワークブックを XML から再読込できないので、表示の試行錯誤は Cloud を描画エンジンにして回す。作業は `outputs/{theme}/refine/`（gitignore 済み）で行う。Cloud 認証は publish-to-cloud Skill の前提に従う。

```
outputs/{theme}/
  prototype/*.html        ドラフト HTML（create-requirements が作る。gitignore 済み）
  refine/
    YYYYWNN.twbx          作業用かつ publish 対象。テーマ直下には .twbx を置かない
    refine.html           refine 中に改訂するドラフト HTML。1 ファイルを上書きで育てる（prototype/ からコピーして始める）
    wb-build/             編集中の TWB（初回に .twbx から展開）
    compare.html          比較ページ（assets/compare.html のコピー。ファイルのまま開く）
    compare-data.js       比較ページが読むドラフト一覧と描画の一覧（iterate.ts が毎回書き直す）
    render/*.png          Cloud の描画
    publish-result.json   publish 結果
    backup/               上書き前の Cloud 版
```

1 ラウンドは次の 1 コマンドで回す:

```bash
npx tsx $SKILL/scripts/iterate.ts --twbx "$THEME_DIR/refine/2026W40.twbx" [--views "Dashboard"] [--patch "$PATCH"]
```

`iterate.ts` は、TWB の整形式チェック → `.twbx` への再梱包 → `publish.py --overwrite --render` を順に行う。`--patch` を付けると `validate-twb.ts` のフィールド参照チェックも走る。XSD 検証は含まないので、Step 4 の 3b を通した後に始める。手作業で作った `.twbx` から始めるときは、それを `refine/YYYYWNN.twbx` に置けばよい。

比較ページは `refine/compare.html` をブラウザでファイルのまま開く（サーバー不要）。左にドラフト HTML（`refine/` と `prototype/` の両方から選べる）、右に Cloud の描画 PNG が並ぶ。

- 一覧は `iterate.ts` が書き出す `compare-data.js` から読む。「Reload both」はこのファイルとドラフト・PNG を読み直す
- ドラフト HTML を足しただけで publish しないときは、`iterate.ts --twbx ... --compare-only` で一覧だけ更新する
- ユーザーと画面を見ながら進めるときは、このページを Chrome で開いて共有する。Claude in Chrome で読むには次の 2 つが要る
  - 拡張機能の詳細で「ファイルの URL へのアクセスを許可する」をオンにする。切り替えると拡張機能が再読み込みされ、既存のタブグループは Claude から見えなくなるので、タブグループは作り直す
  - `navigate` は `file://` を `https://` に書き換えるため使えない。Claude のタブグループに空タブを作り、ユーザーにそのアドレスバーへ file URL を貼ってもらう。以後の読み取り（`get_page_text`・`javascript_tool`・スクリーンショット）は動く
- Claude Code デスクトップの組み込みブラウザは `file://` を静的スナップショットにするため、`compare-data.js` を読めず空になる。使わない

見せ方の変更（レイアウト・文言・情報の削減）は、TWB より先にドラフト HTML で合意する。HTML は数秒で直せ、publish の待ちがない。`prototype/` の原案は要件段階の記録として残し、改訂は `refine/refine.html` を上書きする。版番号は付けない。HTML では Tableau で再現できる表現だけを使う。高さ不足の `#####` や空白の追加のような機械的な修正は、HTML を挟まず TWB を直す。

ループの回し方:

1. `refine/wb-build/*.twb` を直接編集する（生成からやり直すならパッチ JSON を直して Step 4 を再実行する）
2. `iterate.ts` を実行する
3. `renders[].png` を Read し、要件・ドラフト HTML と比べて差分を列挙する。観点は「空白ゾーン」「期待値との一致」「色・線・折り返し」「`#####` 表示」
4. 差分があれば 1 に戻る。空白シートや `#####` の原因は [references/twb-pitfalls.md](references/twb-pitfalls.md) で当たる

PNG は静止画なので、ツールヒント・パラメータ・ハイライト動作は `webpageUrl` をブラウザで開いて確かめる。

Cloud 側の画像キャッシュで前回の絵が返ることがある（1 分未満の連続 publish）。変化が見えないときは 1 分待って `iterate.ts` を再実行する。

### Step 6: Desktop で最終確認

Cloud で表示が固まったら `.twbx` を Tableau Desktop で開いて確認する。Cloud では通るが Desktop が拒否する属性があるため、この確認は省かない。

- 開き直しはユーザーに頼む（Desktop で開いている版は再生成しても更新されない。保存せずに閉じてから開き直す）
- 問題なければ Step 5 の最後の publish が公開版になる。`refine/publish-result.json` の `webpageUrl` を次の `create-x-post` が読む

## パッチJSON仕様

```json
{
  "baseTemplate": "common/WOW Challenge Template (Save a copy) .twbx",
  "outputPath": "outputs/{theme}/refine/2026W40.twbx",
  "workingDir": "outputs/{theme}/refine/wb-build",
  "dataSourceSwap": null,
  "parameters": [
    {
      "name": "Date Granularity",
      "datatype": "string",
      "domainType": "list",
      "values": ["Day", "Week", "Month"],
      "current": "Month"
    }
  ],
  "calculatedFields": [
    {
      "datasource": "federated.0abc",
      "caption": "Profit Ratio",
      "datatype": "real",
      "role": "measure",
      "type": "quantitative",
      "formula": "SUM([Profit])/SUM([Sales])",
      "folder": "2_Stats"
    }
  ],
  "worksheets": [
    {
      "name": "KPI Trend",
      "recipe": "dual-axis",
      "params": {
        "DATASOURCE_NAME": "federated.0abc",
        "FIELD_X": "[Order Date]",
        "FIELD_Y1": "[Sales]",
        "FIELD_Y2": "[Profit Ratio]",
        "COLOR_PRIMARY": "#1f77b4",
        "COLOR_SECONDARY": "#ff7f0e"
      }
    },
    {
      "name": "Custom Sheet",
      "rawXml": "<worksheet name='Custom Sheet'>...</worksheet>"
    }
  ],
  "dashboards": [
    {
      "name": "Main",
      "size": {"width": 1200, "height": 800},
      "sheets": ["KPI Trend", "Custom Sheet"]
    }
  ]
}
```

- `recipe` は `references/chart-recipes/{recipe}.xml` のファイル名から `.xml` を除いたもの
- `recipe`/`rawXml` どちらか一方を指定（両方なら `rawXml` 優先）
- `dataSourceSwap` は Phase 2 で使用、Phase 1 は `null` 固定
- `calculatedFields[].formula` には改行と `//` コメントを書いてよい（TWB では `&#13;&#10;` に変換される）
- `calculatedFields[].folder` を指定すると、データペインのそのフォルダに入る（`<folders-common>` に追記。同名フォルダがあれば合流）。フォルダの切り方は [references/twb-pitfalls.md](references/twb-pitfalls.md) の「計算フィールドの整理」に従う
- `outputPath` は `outputs/{theme}/refine/YYYYWNN.twbx`（WOW の週番号を 2 桁ゼロ埋め）。Cloud 上のワークブック名はこのファイル名から決まる
- `workingDir` を省略すると `refine/wb-build` を使う（`iterate.ts` と同じ場所）

## 参照ファイル

- [references/twb-skeleton-cheatsheet.md](references/twb-skeleton-cheatsheet.md) — TWB XML骨格チートシート
- [references/calc-field-patterns.md](references/calc-field-patterns.md) — 計算フィールド/LOD/パラメータの実例XML
- [references/twb-pitfalls.md](references/twb-pitfalls.md) — XSDを通ってもDesktopで失敗・表示崩れする原因と回避規範（引用符・書式・色・線・テキスト・レイアウト・フォルダ分け）
- [references/chart-recipes/](references/chart-recipes/) — チャート種別ごとのレシピXML（プレースホルダ `{{NAME}}` 形式）
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
- **Phase 1 制約**: データソース置換なし（`dataSourceSwap` は未実装）、レシピは `bar-chart` / `line-chart` / `dual-axis` の3つのみ。レシピで表せないシートは `rawXml` で渡す
- `parameters` はテンプレに `<datasource name='Parameters'>` がある場合のみ挿入できる。現行テンプレには無いので、パラメータを使う出題は別途追加する
- XSD検証は 2025.1 より古い `source-build` のブックを検証できない
- Tableau Desktop自動検証CLIは存在しない。描画の自動確認は Cloud 経由（Step 5）で行い、Desktop での最終確認は手動（Step 6）
