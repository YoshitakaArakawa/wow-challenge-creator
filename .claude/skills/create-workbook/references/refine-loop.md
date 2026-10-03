---
purpose: refine ループの作業フォルダ・比較ページ・ドラフト HTML の運用・描画の読み方
fetched_at: 2026-10-03
note: create-workbook の Step 5 を始めるときに 1 回読む。ループの手順（コマンド、回し方、抜ける前の検算と簡素化レビュー）は SKILL.md の Step 5 が担当し、ここでは重複させない。ユーザーにファイルを開いてもらうときのチャットへの出し方は、リポジトリの CLAUDE.md「ユーザーに開いてもらうもの」が担当する。
---

# refine ループの運用

## 作業フォルダ

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

## 比較ページ

比較ページ `refine/compare.html` は、ユーザーがブラウザでファイルのまま開いて見る（サーバー不要）。左にドラフト HTML（`refine/` と `prototype/` の両方から選べる）、右に Cloud の描画 PNG が並ぶ。

- 初回は、比較ページを開くコマンドをチャットに出す（出し方はリポジトリの CLAUDE.md「ユーザーに開いてもらうもの」）。2 回目以降は、開いたままのページで「Reload both」を押してもらう
- Claude は比較ページを読まない。描画は `render/*.png` と `render/<view>.text.tsv` を直接読む
- 一覧は `iterate.ts` が書き出す `compare-data.js` から読む。「Reload both」はこのファイルとドラフト・PNG を読み直す
- ドラフト HTML を足しただけで publish しないときは、`iterate.ts --twbx ... --compare-only` で一覧だけ更新する

## ドラフト HTML で先に合意する

見せ方の変更（レイアウト・文言・情報の削減）は、TWB より先にドラフト HTML で合意する。HTML は数秒で直せ、publish の待ちがない。`prototype/` の原案は要件段階の記録として残し、改訂は `refine/refine.html` を上書きする。版番号は付けない。HTML では Tableau で再現できる表現だけを使う。高さ不足の `#####` や空白の追加のような機械的な修正は、HTML を挟まず TWB を直す。

ドラフトの横のメモ欄には、いま議論している論点だけを置く（案の切り替え、決めてほしいこと、Tableau での実装の見込み）。合意した変更はドラフト本体に反映してメモから消し、経緯は `refine/HANDOFF.md` に残す。変更点を積み上げると、どこを見てほしいのかが埋もれる。

## 描画の読み方

描画は、確かめたい内容に合う形で読む。PNG を毎回全体で読む必要はない。

| 確かめたいこと | 読むもの | 取り方 |
|---|---|---|
| レイアウト・余白・重なり・全体の印象 | ダッシュボードの PNG | `--views "<ダッシュボード名>"` |
| 直したシートの見た目 | そのシートの PNG | `--views "<シート名>"`。シートは単体の大きさで描かれるので、配置はダッシュボードで見る |
| 文字の色・サイズ・太さ・文言（書式が指定どおりか、色が何種類あるか） | `render/<view>.text.tsv` | `--text-table` を付ける。PNG より少ないトークンで、色コードとピクセル値が正確に出る |

文字の表は、書式を確かめる必要があるときだけ取る。表に出ない配置や見た目は PNG で見る。

Cloud 側の画像キャッシュで前回の絵が返ることがある（1 分未満の連続 publish）。変化が見えないときは 1 分待って `iterate.ts` を再実行する。
