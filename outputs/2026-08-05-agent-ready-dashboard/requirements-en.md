# WOW2026 W31: Can You Build an Agent-Ready Dashboard?

## Introduction

I have been running an experimental fork of the Tableau MCP server, trying to make dashboards live inside an AI chat. The piece I am most excited about is the viz state snapshot. You filter the embedded dashboard, the model gets told what you are now looking at, and it can go query the data source behind it. The dashboard stops being the end of the conversation and becomes something you and the agent are looking at together.

A dashboard built for that spot has to be small and it has to explain itself, because it turns up mid-conversation with nobody there to walk you through it. So this week, build one at close to a mobile size. On top of that, let's try Tableau Public's published data sources, which are new. Connecting to one is something you can only do in the browser, so this challenge is Web Authoring the whole way and Tableau Desktop stays closed. And since the chat app picks the width, the size below is a range rather than a fixed number.

## Requirements

- Set up
  - Dashboard size: Range, 650 x 800 minimum, 750 x 900 maximum
  - Build it entirely in Tableau Public Web Authoring, no Tableau Desktop
  - Connect to the published Sample Superstore 2026.2 data source, no file uploads
  - 5 sheets
- Controls
  - Year Month, Region and Segment as single select dropdowns across the top
  - One parameter, Selected Measure, listing Sales / Profit / Profit Ratio and starting on Profit Ratio
- The view
  - A KPI row showing Sales, Profit and Profit Ratio, measure name above the value
  - Bars of the selected measure by Sub-Category, sorted descending, colored so negatives read as negative
  - Bar values in a fixed width column to the right of the chart, right edges aligned on every row
- Finishing touches
  - A light gray band behind the KPI row and behind the parameter control
  - Tooltips that stand alone: the sub-category, the name of the selected measure, and the value
  - Match the tooltips and formatting as closely as possible

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>

<p>I have been running an experimental fork of the Tableau MCP server, trying to make dashboards live inside an AI chat. The piece I am most excited about is the viz state snapshot. You filter the embedded dashboard, the model gets told what you are now looking at, and it can go query the data source behind it. The dashboard stops being the end of the conversation and becomes something you and the agent are looking at together.</p>

<p>A dashboard built for that spot has to be small and it has to explain itself, because it turns up mid-conversation with nobody there to walk you through it. So this week, build one at close to a mobile size. On top of that, let's try Tableau Public's published data sources, which are new. Connecting to one is something you can only do in the browser, so this challenge is Web Authoring the whole way and Tableau Desktop stays closed. And since the chat app picks the width, the size below is a range rather than a fixed number.</p>

<h2>Requirements</h2>

<h3>Set up</h3>

<ul>
<li>Dashboard size: Range, 650 x 800 minimum, 750 x 900 maximum</li>
<li>Build it entirely in Tableau Public Web Authoring, no Tableau Desktop</li>
<li>Connect to the published Sample Superstore 2026.2 data source, no file uploads</li>
<li>5 sheets</li>
</ul>

<h3>Controls</h3>

<ul>
<li>Year Month, Region and Segment as single select dropdowns across the top</li>
<li>One parameter, Selected Measure, listing Sales / Profit / Profit Ratio and starting on Profit Ratio</li>
</ul>

<h3>The view</h3>

<ul>
<li>A KPI row showing Sales, Profit and Profit Ratio, measure name above the value</li>
<li>Bars of the selected measure by Sub-Category, sorted descending, colored so negatives read as negative</li>
<li>Bar values in a fixed width column to the right of the chart, right edges aligned on every row</li>
</ul>

<h3>Finishing touches</h3>

<ul>
<li>A light gray band behind the KPI row and behind the parameter control</li>
<li>Tooltips that stand alone: the sub-category, the name of the selected measure, and the value</li>
<li>Match the tooltips and formatting as closely as possible</li>
</ul>

-->
