---
name: create-requirements
description: WOW出題の要件文(英語+日本語+HTML埋め込み版)を作成する。必要に応じてHTML/Chart.jsプロトタイプも作成し、Vizイメージの認識合わせに使う。「要件を書いて」「問題文を作って」「プロトタイプを見せて」「イメージを見たい」で使用。
---

# WOW要件作成スキル

ブレストで確定したテーマを正式な要件文（Introduction + Requirements）に仕立てる。必要ならHTMLプロトタイプも併産する。

## 手順

### 1. 前提確認
- 出題フォルダ `outputs/YYYY-MM-DD-theme-name/` が存在するか
- テーマ・難易度・使用機能・データセットが決まっているか（未決定なら `brainstorm` スキルに戻す）
- 既存Vizを参考にする場合は事前に `analyze-twbx` で解析しておくと精度が上がる

### 2. 要件文の作成

`wow-style-guide.md` を必ず参照してWOW標準のスタイルで作成する。

- まず**日本語**でユーザーと内容を詰める → `requirements-ja.md`
- 確定後、**英語**版を作成（直訳ではなく、WOWコミュニティのトーンに合わせる） → `requirements-en.md`
- スコープは **Introduction** と **Requirements** の2セクションのみ
- 英語版MDファイルの末尾に、HTMLコメントとしてサイト掲載用のHTML版を埋め込む（詳細はスタイルガイド参照）

作成後、ユーザーに提示してレビュー。

### 3. プロトタイプHTMLの作成（任意）

Vizのレイアウト・線の本数・色分け・BAN配置などを事前に視覚化したい場合に作る。

- 出題フォルダに `prototype.html` として保存
- Chart.js / vanilla HTML / SVG など軽量な手段で実装
- 参考: `outputs/2026-03-25-viz-extensions-dashboard/prototype.html`
- 「プロトを作って」「イメージを見たい」とユーザーから言われた時、または要件確定前に認識合わせが必要そうな場合に提案

### 4. 成果物

| ファイル | 説明 |
|---|---|
| `outputs/{theme}/requirements-ja.md` | 日本語版（先に作成） |
| `outputs/{theme}/requirements-en.md` | 英語版 + 末尾にHTMLコメント埋め込み |
| `outputs/{theme}/prototype.html` | 任意。Vizイメージの事前可視化 |

これらは後続の `create-workbook` および `create-x-post` の入力になる。

## 参照
- スタイルガイド: [wow-style-guide.md](wow-style-guide.md)
