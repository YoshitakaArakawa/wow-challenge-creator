# WOW2026 W47: Let's Build a Converging Sankey!

## はじめに

Tableau Data Apps で遊んでいたら、AI が Profit をサンキーダイアグラムで描いてくれました。ふだんサンキーを使うときは、売上のような正の値を流します。ところが AI は、Profit のように負になる値もそのまま扱って表示してくれました。これを Tableau のワークブックでも再現してみたくなりました。

今回は、負の値も扱えるサンキーダイアグラムを作ります。楽しんでください！

## 要件

- ダッシュボードサイズ: 800 x 1000
- Ship Mode と Region のフィルターを、すべての要素に適用する
  - Same Day と Central を選ぶと、Furniture だけ純額がマイナスになる。この組み合わせでも描けることを確かめる
- データの 1 行（明細行。Order ID 単位ではない）ごとに、Profit が 0 以上なら Gains、負なら Loss とする。帯の幅は、どちらも金額の絶対値で測る
- カテゴリは、純額の小さい順に左から並べる
- 帯は、いちばん上と下で Net Profit の棒に収束する。Gains と Loss は打ち消し合い、小さいほうの帯は消え、大きいほうの帯は純額の幅だけ残る
  - たとえば Furniture は Gains $81,405、Loss $61,675 なので、Gains の帯だけが $19,730 分の幅で残ります
- 収束しない普通のサンキーまで作った[スターター](https://public.tableau.com/app/profile/yoshitaka6076/viz/WOW2026W47Starter/WOW2026W47)から始めてもかまいません

## ヒント

帯が Net の棒に収束するところを、よく見てください。帯は、反対側の帯の幅だけ細くなっています。鍵になる計算は、この反対側の幅です。Gains の帯なら Loss の幅、Loss の帯なら Gains の幅を求めます。これは表計算で取れます。

チャレンジよりも作り方を学びたい方は、手順書もどうぞ。スターターから完成までをシート 1 枚ずつ、設定を図で細かく載せています。ほぼ答えそのものなので、自力で解きたい方は最後に見てください。

- 日本語: https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-ja.html
- English: https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-en.html

## データセット

Sample - Superstore（2026.2）
