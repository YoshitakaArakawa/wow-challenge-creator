# WOW2026 W47: Let's Build a Converging Sankey!

## Introduction

I was playing around with Tableau Data Apps when an AI assistant drew Profit as a Sankey diagram. When I use a Sankey diagram, I usually show positive values like Sales. But the AI took Profit, a value that can go negative, and displayed it just fine. I wanted to recreate this in a Tableau workbook.

In this challenge, you'll build a Sankey diagram that handles negative values too. Have fun with it!

## Requirements

- Dashboard size: 800 x 1000 px
- Add filters for Ship Mode and Region, and apply them to all sheets
  - Selecting Ship Mode = Same Day and Region = Central makes only Furniture's net amount negative. Check that your viz still works with this combination
- Split each row of the data (each order line, not each Order ID) by the sign of its Profit. 0 or above is Gains, below 0 is Loss. Size both by the absolute value
- Sort the categories from left to right by net amount, smallest first
- The bands converge into the Net Profit bars at the top and at the bottom. Gains and Loss cancel each other out. The smaller band disappears, and the larger one keeps only the width of the net amount
  - For example, Furniture has $81,405 in Gains and $61,675 in Loss, so only the Gains band remains, $19,730 wide
- You're welcome to start from the [starter workbook](https://public.tableau.com/app/profile/yoshitaka6076/viz/WOW2026W47Starter/WOW2026W47), which already contains a standard, non-converging Sankey

## Hints

Take a close look where the bands converge into the Net bars. Each band gets narrower by the width of the band on the opposite side. So the key calculation is that opposite width: the Loss width for a Gains band, and the Gains width for a Loss band. A table calculation can get it.

If you'd rather learn the technique than take on the challenge, try the step-by-step guide. It goes from the starter to the finished viz one sheet at a time, with the settings shown visually in detail. It's close to a full answer, so if you want to solve it on your own, save it for last.

- English: https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-en.html
- 日本語: https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-ja.html

## Dataset

Sample - Superstore (2026.2)

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>I was playing around with Tableau Data Apps when an AI assistant drew Profit as a Sankey diagram. When I use a Sankey diagram, I usually show positive values like Sales. But the AI took Profit, a value that can go negative, and displayed it just fine. I wanted to recreate this in a Tableau workbook.</p>
<p>In this challenge, you'll build a Sankey diagram that handles negative values too. Have fun with it!</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 800 x 1000 px</li>
<li>Add filters for Ship Mode and Region, and apply them to all sheets
<ul>
<li>Selecting Ship Mode = Same Day and Region = Central makes only Furniture's net amount negative. Check that your viz still works with this combination</li>
</ul>
</li>
<li>Split each row of the data (each order line, not each Order ID) by the sign of its Profit. 0 or above is Gains, below 0 is Loss. Size both by the absolute value</li>
<li>Sort the categories from left to right by net amount, smallest first</li>
<li>The bands converge into the Net Profit bars at the top and at the bottom. Gains and Loss cancel each other out. The smaller band disappears, and the larger one keeps only the width of the net amount
<ul>
<li>For example, Furniture has $81,405 in Gains and $61,675 in Loss, so only the Gains band remains, $19,730 wide</li>
</ul>
</li>
<li>You're welcome to start from the <a href="https://public.tableau.com/app/profile/yoshitaka6076/viz/WOW2026W47Starter/WOW2026W47">starter workbook</a>, which already contains a standard, non-converging Sankey</li>
</ul>

<h2>Hints</h2>
<p>Take a close look where the bands converge into the Net bars. Each band gets narrower by the width of the band on the opposite side. So the key calculation is that opposite width: the Loss width for a Gains band, and the Gains width for a Loss band. A table calculation can get it.</p>
<p>If you'd rather learn the technique than take on the challenge, try the step-by-step guide. It goes from the starter to the finished viz one sheet at a time, with the settings shown visually in detail. It's close to a full answer, so if you want to solve it on your own, save it for last.</p>
<ul>
<li>English: <a href="https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-en.html">https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-en.html</a></li>
<li>日本語: <a href="https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-ja.html">https://yoshitakaarakawa.github.io/wow-challenge-creator/outputs/2026-11-25-converging-sankey/guide/starter-walkthrough-ja.html</a></li>
</ul>

<h2>Dataset</h2>
<p>Sample - Superstore (2026.2)</p>

-->
