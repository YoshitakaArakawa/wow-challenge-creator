# WOW2026 W12: Can You Create a Gauge Chart with Tableau Extensions?

## Introduction

Tableau 2025.3でRadial Viz ExtensionにSunburstが追加されたので触ってみたところ、Gauge Chartも簡単に作れることに気づきました。調べてみると、実は2024.2のRadial Extension登場時からできたらしいです。

Tableauでゲージチャートを作るにはマップレイヤーや専用のデータ準備が必要で、なかなか大変でした。Radial Extensionならずっとシンプルに実現できるので、WOWで紹介する価値があると思い今回のチャレンジにしました。Extensionsに馴染みがなくても取り組みやすい内容なので、ぜひ試してみてください。

## Requirements

- ダッシュボードサイズ: 1200 x 800
- シート数は任意
- Sample - SuperstoreのデータとBudget CSV（Data sectionを参照）を結合して使用する
- 3つのゲージチャート（Furniture / Office Supplies / Technology）をRadial Viz Extensionで作成し、Achievement %（達成率）を表示する
- Category別のSub-Categoryの売上を棒チャートで表示し、Budgetをリファレンスラインとして配置する
- YearMonth、Region、Segmentのフィルタを配置する
- ツールチップとフォーマットをできる限り一致させること

## Hints

Radial Viz Extensionの使い方に迷ったら、こちらの記事が参考になります:

- [Tableau's New Radial Chart Type | Tableau 2024.2 and Newer - TableauTim](https://www.tableautim.com/playlist-video/tableau-s-new-radial-chart-type-tableau-2024-2-and-newer)
