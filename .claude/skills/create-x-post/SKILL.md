---
name: create-x-post
description: WOW出題の公開告知用X(Twitter)投稿文を作成する。280文字以内、`#WOW{YYYY} #Tableau Week N is live!` で始まり、Vizそのものに焦点を当てた誘い文句を含める。「X投稿文を作って」「告知文書いて」「ツイートして」で使用。
---

# X投稿文作成スキル

出題公開時にXへ投稿する告知文を作成する。

## 制約
- **半角280文字以内**（URLは1つ25文字換算、本文は200文字程度を目安）
- `#WOW{YYYY} #Tableau Week N is live!` から開始
- 必ず出題URLを含める

## 入力

| ファイル | 用途 |
|---|---|
| `outputs/{theme}/requirements-en.md` | テーマ・難易度・特徴を把握 |
| `outputs/{theme}/tmp/publish-result.json` | publish-to-cloud が出力。`webpage_url` を埋め込む（あれば） |
| WOW公式サイトURL | サイト掲載後はそちらを優先 |

## トーン・表現ガイド

### 避ける
- em dash（`—`）をつなぎに使う（AI生成感が出るため。ピリオドやコンマで区切る）
- 説教臭い・上から目線（例: 「Before AI analyzes...」のような言い回しはNG）
- 細かい仕様（prior month, prior yearなど）の列挙
- KPIなど具体的なテーマの強調

### 推奨
- **Viz（ビジュアライゼーション）そのもの** に焦点を当てる
- 人を誘う表現を使う（`Let's build...`、`Try...`、`Give it a try!`）
- 気軽さの演出（`Quick & light`、`Have fun!`、`Enjoy!`）
- シンプルに、短く

## 構成例

```
#WOW{YYYY} #Tableau Week N is live!

[誘い文句 — Let's build... / Try building...]

[難易度・トーン — Quick & light... / Have fun!]

[URL]
```

## 参考
@WorkoutWednsday の過去投稿を確認してトーンを合わせる。

## 出力
出題フォルダの `x-post.txt` として保存。半角280文字以内であることを必ず確認する。
