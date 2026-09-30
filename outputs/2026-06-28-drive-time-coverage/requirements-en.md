# WOW2026 W26: Let's Try the Drive Time Area

## Introduction

Tableau 2026.2 added a new Drive Time Area tool to maps, and I couldn't resist building a challenge around it. You click a spot, drag outward, and Tableau shows how far you can really drive based on actual roads, not a straight line circle. This week, start from Union Station in Washington D.C. and find out how many grocery stores fall within your drive. Give it a try!

Note that the Drive Time Area tool is not available in Tableau Public web authoring at this time. Please use Tableau Desktop or Tableau Desktop Public Edition.

## Requirements

- Dashboard size: 1000 x 800
- 2 sheets
- Plot the grocery stores in Washington D.C. on a map
- Show a map of the District of Columbia only
    - Hint: The Superstore dataset has a State column, right?
    - Hint: See "Multi data sources in map layers": https://www.tableau.com/2021-4-features#item-86380
- Mark the origin point (Union Station) on the map
    - Its (Latitude, Longitude) is (38.8977, -77.0063)
- Show the total number of stores in the data and the number of stores inside the Drive Time Area
- Color the stores by whether they fall inside the Drive Time Area
- Match the tooltips and formatting as closely as possible

## Dataset

This challenge uses a dataset of grocery stores in Washington D.C. You can download the data here (GitHub: https://github.com/Workout-Wednesday/data/blob/main/2026/dc-grocery-clean.csv).

![How to download the dataset from GitHub](<GitHub How to Download Dataset.png>)

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>Tableau 2026.2 added a new Drive Time Area tool to maps, and I couldn't resist building a challenge around it. You click a spot, drag outward, and Tableau shows how far you can really drive based on actual roads, not a straight line circle. This week, start from Union Station in Washington D.C. and find out how many grocery stores fall within your drive. Give it a try!</p>
<p>Note that the Drive Time Area tool is not available in Tableau Public web authoring at this time. Please use Tableau Desktop or Tableau Desktop Public Edition.</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 1000 x 800</li>
<li>2 sheets</li>
<li>Plot the grocery stores in Washington D.C. on a map</li>
<li>Show a map of the District of Columbia only
  <ul>
  <li>Hint: The Superstore dataset has a State column, right?</li>
  <li>Hint: See "Multi data sources in map layers": https://www.tableau.com/2021-4-features#item-86380</li>
  </ul>
</li>
<li>Mark the origin point (Union Station) on the map
  <ul>
  <li>Its (Latitude, Longitude) is (38.8977, -77.0063)</li>
  </ul>
</li>
<li>Show the total number of stores in the data and the number of stores inside the Drive Time Area</li>
<li>Color the stores by whether they fall inside the Drive Time Area</li>
<li>Match the tooltips and formatting as closely as possible</li>
</ul>

<h2>Dataset</h2>
<p>This challenge uses a dataset of grocery stores in Washington D.C. You can download the data here (GitHub: https://github.com/Workout-Wednesday/data/blob/main/2026/dc-grocery-clean.csv).</p>
<p><img src="GitHub How to Download Dataset.png" alt="How to download the dataset from GitHub"></p>

-->
