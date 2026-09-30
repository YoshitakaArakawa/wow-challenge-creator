# WOW2026 W26: Let's Try the Drive Time Area

## Introduction

Tableau 2026.2 で、マップに新しい Drive Time Area ツールが加わりました。地点をクリックして外側へドラッグするだけで、実際の道路網に沿った「車での到達圏」をその場で描き、圏内のマークを選択できます。直線距離の円とは違い、川や道路の事情を反映した現実的な範囲が出るのが面白いところです。

今回は Washington D.C. の食料品店データを使って、この新機能を気軽に試してみましょう。地図上の起点(Union Station)から Drive Time Area を広げ、その中にいくつ食料品店が入るかを数えます。新機能の操作に加えて、選択をセットアクションでセットに焼き込み、BAN に集計する流れも学べます。はじめての地図系チャレンジにもちょうどいい難易度です。

なお、現時点では Drive Time Area は Tableau Public の Web 編集では使えません。Tableau Desktop または Tableau Desktop Public Edition で取り組んでください。

## Requirements

- ダッシュボードサイズ: 1000 x 800
- シート2枚
- Washington D.C.の食料品店を地図に表示する
- District of Columbiaだけの地図が表示されるようにする
    - Hint: Superstore DatasetにはState列がありますよね？
    - Hint: See "Multi data sources in map layers" — https://www.tableau.com/2021-4-features#item-86380
- 起点となる地点(Union Station)をマップ上にポイントで示す
    - Its (Latitude, Longitude) is (38.8977, -77.0063)
- データ中の店舗数の総数と、Drive Time Areaに含まれる店舗の数を表示する
- Drive Time Areaに含まれる店舗とそれ以外で、店舗を色分けする
- Match the tooltips and formatting as closely as possible

## Dataset

This challenge uses a dataset of grocery stores in Washington D.C. You can download the data here (GitHub: https://github.com/Workout-Wednesday/data/blob/main/2026/dc-grocery-clean.csv).

![How to download the dataset from GitHub](<GitHub How to Download Dataset.png>)
