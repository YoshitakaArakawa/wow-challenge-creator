---
purpose: apply-edits.ts が読むパッチ JSON（workbook-patch.json）の書式
fetched_at: 2026-10-03
note: create-workbook の Step 3 でパッチを起案するときに読む。パッチで表せるのは計算フィールドの足場まで。シート・ダッシュボード・パラメータは TWB の直接編集で書く（twb-skeleton-cheatsheet.md）。
---

# パッチ JSON 仕様

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
- `calculatedFields[].folder` を指定すると、データペインのそのフォルダに入る（`<folders-common>` に追記。同名フォルダがあれば合流）。フォルダの切り方は [twb-pitfalls.md](twb-pitfalls.md) の「計算フィールドの整理」に従う
- `calculatedFields[].defaultFormat` は既定の数値書式（省略可）。動作確認済みの書式は twb-pitfalls.md の「数値書式」
- `calculatedFields[].datasource` は省略する。省略すると、テンプレの主データソース（`Parameters` 以外で最初のもの）に入る
- 内部名は `[Calculation_001]` からパッチの並び順に振られる。式の中の計算フィールド参照はこの内部名で書く（`apply-edits.ts` はキャプションを内部名に置き換えない）
- `worksheets[]`（`name` と `rawXml`）と `dashboards[]`（`name`・`size`・`sheets`）も書けるが、ダッシュボードは全シートを縦に等分するだけになる。通常は使わず、直接編集で書く
- `outputPath` は `outputs/{theme}/refine/YYYYWNN.twbx`（WOW の週番号を 2 桁ゼロ埋め）。Cloud 上のワークブック名はこのファイル名から決まる
- `workingDir` を省略すると `refine/wb-build` を使う（`iterate.ts` と同じ場所）
