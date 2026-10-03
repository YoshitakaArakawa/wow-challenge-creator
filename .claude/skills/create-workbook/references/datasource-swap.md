---
purpose: テンプレのデータソースを出題のデータに差し替える手順と、複数の指標を Pivot する手順
sources:
  - https://github.com/tableau/tableau-document-schemas
fetched_at: 2026-10-03
source_last_known_update: 不明
note: create-workbook の Step 4 で、TWB のデータソース（接続・抽出・relation・metadata-records）を書き換えるときの手順だけを扱う。シートやダッシュボードの骨格は twb-skeleton-cheatsheet.md、表示が崩れる落とし穴は twb-pitfalls.md が担当する。
---

# データソースの差し替えと Pivot

Pivot は、差し替えで直接接続にしてから行う。

## 同梱 Excel への直接接続に差し替える

テンプレのデータソースは hyper 抽出を持ち、元の Excel への接続は作者のマシンのパスを指している。抽出の中身は抽出した時点のデータで、要件が指定する期間を含まないことがある。出題のデータを使うときは、Excel を `.twbx` に同梱し、抽出を外して直接接続にする。

1. 出題のデータ（`common/Sample - Superstore.xlsx`）を `refine/wb-build/Data/Superstore/` にコピーする。
2. `<named-connection>` の中の `<connection class='excel-direct'>` の `filename` を、`wb-build` からの相対パスに書き換える。
3. `<datasource>` の中の `<extract …>` から `</extract>` までを丸ごと削除する（`<folders-common>` の後、`<layout>` の前にある）。`<object-graph>` の中の `<properties context='extract'>…</properties>` も削除し、`<properties context=''>` だけを残す。
4. `refine/wb-build/Data/Downloads/` の hyper ファイルを取り除く。

```xml
<named-connection caption='Sample - Superstore' name='excel-direct.xxxx'>
  <connection class='excel-direct' cleaning='no' compat='no' dataRefreshTime=''
      filename='Data/Superstore/Sample - Superstore.xlsx' interpretationMode='0' password='' server='' validate='no' />
</named-connection>
```

- 差し替えられるのは、シート名（`Orders`）と列の構成がテンプレと同じ Excel だけ。`<relation table='[Orders$]'>` と `<columns>`、`<metadata-records>` はそのまま使う。列の構成が違うデータへの差し替えは対象外。

## Pivot

複数の指標（Sales / Profit など）を1組の計算でまかなうときは、テーブルの relation を `type='pivot'` の relation で包む。`<connection>` 内と `<object-graph>` 内の2か所に同じ relation がある。

```xml
<relation name='Pivot' type='pivot'>
  <columns>
    <column datatype='string' name='Pivot Field Names' />
    <column datatype='real' name='Pivot Field Values' />
  </columns>
  <tag name='Pivot Field Names'>
    <value name='[Profit]' />
    <value name='[Sales]' />
  </tag>
  <groups>
    <group name='Pivot Field Values'>
      <field name='[Orders].[Profit]' />
      <field name='[Orders].[Sales]' />
    </group>
  </groups>
  <relation connection='…' name='Orders' table='[Orders$]' type='table'>…</relation>
</relation>
```

- `<metadata-records>` から元の列（Sales / Profit）のレコードを外し、`Pivot Field Names`（string）と `Pivot Field Values`（real）のレコードを足す。どちらも `parent-name` は `[Pivot]`、`object-id` は他の列と同じにする。他の列の `parent-name` は `[Orders]` のままでよい。

```xml
<metadata-record class='column'>
  <remote-name>Pivot Field Names</remote-name>
  <remote-type>129</remote-type>
  <local-name>[Pivot Field Names]</local-name>
  <parent-name>[Pivot]</parent-name>
  <remote-alias>Pivot Field Names</remote-alias>
  <ordinal>20</ordinal>
  <local-type>string</local-type>
  <aggregation>Count</aggregation>
  <contains-null>true</contains-null>
  <object-id>[Orders_xxxx]</object-id>
</metadata-record>
```

- テンプレの `0_raw` フォルダにある `[Sales]` / `[Profit]` の `folder-item` は、残したままでも動く。
- 表示名は `<datasource>` 直下の `<column caption='Metric' name='[Pivot Field Names]' …/>` で付ける。計算式からは `[Pivot Field Names]` / `[Pivot Field Values]` で参照する。
