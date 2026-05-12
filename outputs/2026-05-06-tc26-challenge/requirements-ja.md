# WOW2026 W18: TC26のAIウェーブを可視化できますか？

## Introduction

このチャレンジはTC26のWorkout Wednesdayセッションで公開されました。
会場の方も、後日この問題に出会った方も、ぜひ楽しんでいってください。

このチャレンジではTableau Conferenceのセッションを可視化します。3つの難易度を用意したので、ご自身の自信に合わせてチャレンジしてみてください。早速問題に入りましょうか！

## Requirements

- Dashboard size: 1000 x 800
- データソース: `sessions.csv`
- AI関連セッションは、以下のいずれかに該当するもの:
    - タイトルに `AI` もしくは `Agent` を含む
    - Topicが `Agentic Analytics` もしくは `Artificial Intelligence`
- BAN: TC26全体のセッションに対するAI関連セッションの割合を表示する
- Calendar:
    - 縦軸はセッション開始時刻
    - 同じ開始時刻のセッションは、AI関連セッションを左側に配置する

### Bonus

- BAN: セッション数ではなくセッション時間の合計ベースで割合を算出し直す
- Calendar: 円のサイズをセッション時間に応じて変化させる
- Calendar: 各日付パネル内で、同じ開始時刻の円をセッション時間順に並べ替える。並びはAI関連グループと非AIグループの境界でリセットする
- Tooltip: セッションタイトルの文字色を、対応する円の色（AI関連 / 非AI）に合わせて変更する

### Extreme

- データをMay 5のセッションのみに絞る
- Calendarをスペース効率重視のGantt形式で構築する:
    - 縦軸: 時刻
    - 各セッション: 開始〜終了時刻を結ぶ縦線
- 重なるセッションは横方向の列にスタックする:
    - 時間的に重なる場合は、すぐ右の列に配置する
    - 重なりが途切れたら、次のセッションを一番左の列まで戻す
- ヒント:
    - 付属の `minutes.csv` を sessions と組み合わせてデータを密度化する
    - 重なりの定義: 現在のセッションの開始時刻 ≤ 直前のセッションの終了時刻
    - ネストした表計算と `PREVIOUS_VALUE()` が必要
    - アルゴリズムの詳細は [Space-Effective Gantt Chart](https://www.yarakawa.com/single-post/space_effective_gantt_chart) の「まずはリセットしながら積み上げる」セクションを参照

## Dataset

This challenge uses a dataset built from the **TC25 (Tableau Conference 2025) public session catalogue**, originally shared in the Tableau blog post (https://www.tableau.com/blog/3-steps-to-viz-your-tableau-conference-schedule). 
You can download the data here (Google Drive: TODO).