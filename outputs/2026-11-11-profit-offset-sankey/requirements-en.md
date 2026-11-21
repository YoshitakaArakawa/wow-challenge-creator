# WOW2026 W47: Let's Build a Converging Sankey!

## Introduction

I was playing around with Tableau Data Apps and an AI assistant when the AI drew profit as a Sankey diagram. Even the order lines that lost money flowed as bands, canceling out the profitable ones and converging into the net amount. A Sankey uses band width to show quantity, so I had assumed it couldn't handle negative values. I wanted to recreate this in a Tableau workbook.

In this challenge, you'll build a Sankey diagram that handles negative values too. If you need a refresher on the basics, Olivier Catherin's [Polygon Sankey](https://www.dataplusscience.com/SankeyPolygon.html) is a good place to start. Have fun with it!

## Requirements

- Dashboard size: 800 x 1000 px
- Add filters for Ship Mode and Region, and apply them to all sheets
  - Selecting Ship Mode = Same Day and Region = South makes the net amount negative. Check that your viz still works with this combination
- Split each row of the data (each order line, not each Order ID) by the sign of its Profit. 0 or above is Gains, below 0 is Loss. Size both by the absolute value
- Sort the categories from left to right by net amount, smallest first
- The bands converge into the Net Profit bars at the top and at the bottom. Gains and Loss cancel each other out. The smaller band disappears, and the larger one keeps only the width of the net amount
  - Hint: The only difference from a standard Sankey is the width at the converging end. For each band, subtract the width of the opposite sign in the same group (the whole, or the category). For example, Furniture has $81,405 in Gains and $61,675 in Loss, so only the Gains band remains, $19,730 wide. Line up the remaining band with the edge where Loss meets Gains (at the bottom, the edge inside each category)

## Dataset

Sample - Superstore (2026.2)

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>I was playing around with Tableau Data Apps and an AI assistant when the AI drew profit as a Sankey diagram. Even the order lines that lost money flowed as bands, canceling out the profitable ones and converging into the net amount. A Sankey uses band width to show quantity, so I had assumed it couldn't handle negative values. I wanted to recreate this in a Tableau workbook.</p>
<p>In this challenge, you'll build a Sankey diagram that handles negative values too. If you need a refresher on the basics, Olivier Catherin's <a href="https://www.dataplusscience.com/SankeyPolygon.html">Polygon Sankey</a> is a good place to start. Have fun with it!</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 800 x 1000 px</li>
<li>Add filters for Ship Mode and Region, and apply them to all sheets
<ul>
<li>Selecting Ship Mode = Same Day and Region = South makes the net amount negative. Check that your viz still works with this combination</li>
</ul>
</li>
<li>Split each row of the data (each order line, not each Order ID) by the sign of its Profit. 0 or above is Gains, below 0 is Loss. Size both by the absolute value</li>
<li>Sort the categories from left to right by net amount, smallest first</li>
<li>The bands converge into the Net Profit bars at the top and at the bottom. Gains and Loss cancel each other out. The smaller band disappears, and the larger one keeps only the width of the net amount
<ul>
<li>Hint: The only difference from a standard Sankey is the width at the converging end. For each band, subtract the width of the opposite sign in the same group (the whole, or the category). For example, Furniture has $81,405 in Gains and $61,675 in Loss, so only the Gains band remains, $19,730 wide. Line up the remaining band with the edge where Loss meets Gains (at the bottom, the edge inside each category)</li>
</ul>
</li>
</ul>

<h2>Dataset</h2>
<p>Sample - Superstore (2026.2)</p>

-->
