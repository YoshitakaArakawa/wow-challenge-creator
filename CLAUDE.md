# WOW Challenge Creator

Workout Wednesday (WOW) Tableau出題を作成するための支援環境。

## Workout Wednesday とは

毎週水曜日に公開されるTableauスキルチャレンジ。参加者は提示されたビジュアライゼーションを可能な限り再現する。難易度は初級から上級まで幅広く、グローバルコミュニティで人気。

## 共通ルール

1. **直近3回と被らない** - 出題前に必ずWeb検索で確認
2. **難易度はユーザーが指定** - 問題作成時に確認する
3. **要件は英語＋日本語** - 英語で作成し、日本語も併記

## 参照URL

| 情報 | URL |
|------|-----|
| WOW Tableau出題 | https://workout-wednesday.com/category/tableau/ |
| Tableau最新機能 | https://www.tableau.com/products/new-features |
| Tableau全リリース一覧 | https://www.tableau.com/products/all-features |

## ワークフロー

### Step 1: 出題フォルダの作成
`outputs/` に出題用フォルダを作成する。

**命名規則**: `YYYY-MM-DD-テーマ名`（英語ケバブケース）
- 例: `outputs/2026-02-05-sankey-drilldown/`
- テーマが未定の場合は仮名で作成し、確定後にリネーム

**フォルダ構成**:
```
outputs/YYYY-MM-DD-theme-name/
├── requirements-ja.md   # 要件文（日本語・先に作成）
├── requirements-en.md   # 要件文（英語・日本語確定後に作成）
├── discussion.md        # ブレスト・検討の議事録
└── *.twbx               # ユーザーが作成したワークブック（手動配置）
```

### Step 2: ブレスト
→ `.claude/skills/brainstorm/SKILL.md` を使用

重複チェック → ヒアリング → アイデア展開。結果は `discussion.md` に記録。

### Step 2.5: プロトタイプ作成（任意）
ブレストでVizの方向性が固まったら、Tableau実装前にHTML + Chart.js等でレイアウトのプロトタイプを作成できる。
- 出題フォルダに `prototype.html` として保存
- BAN配置、チャートの線の本数・色分け、軸の構成などを素早く視覚化し、認識合わせに使う
- ユーザーが「イメージを見たい」「プロトを作って」と言った場合に実施

### Step 3: 要件作成＋解析
→ `.claude/skills/create-challenges/SKILL.md` を使用

決定したテーマを正式な要件文に。必要に応じてTableau Public MCPで既存Vizを解析。結果は `requirements.md` に保存。

### Step 4: X投稿文の作成
出題公開時にXへ投稿する告知文を作成する。

**制約**:
- 半角280文字以内（URLは1つ25文字換算、本文は200文字程度を目安）
- `#WOW2026 #Tableau Week N is live!` から開始

**参考**: @WorkoutWednsday の過去投稿を確認し、トーンを合わせる

**保存先**: 出題フォルダに `x-post.txt` として保存

**トーン・表現のガイドライン**:
- em dash（`—`）をつなぎに使わない（AI生成感が出るため。ピリオドやコンマで区切る）
- 説教臭い・上から目線の表現は避ける（例: 「Before AI analyzes...」のような言い回しはNG）
- KPIなど具体的なテーマよりも **Viz（ビジュアライゼーション）そのもの** に焦点を当てる
- 人を誘う表現を使う（`Let's build...`、`Try...`、`Give it a try!`）
- 細かい仕様（prior month, prior year等）は書かず、シンプルに留める
- 気軽さを演出（`Quick & light`、`Have fun!`、`Enjoy!`）

**構成例**:
```
#WOW2026 #Tableau Week N is live!

[誘い文句 - Let's build... / Try building...]

[難易度・トーン - Quick & light... / Have fun!]

[URL]
```
