# WOW2026 W{N}: Can You Build a Weekly Question-First Dashboard?

## Introduction

With AI agents and mobile notifications, we open dashboards to go exploring less and less. I think BI is heading toward something closer to a weekly message on your phone: the answers to a few questions everyone on the team should know. If that's true, the first design decision isn't the chart type. It's which questions you answer.

So this week, we'll take one week of Superstore and answer four shared questions, each with a Yes / No, a number and a small chart. Weekly numbers are noisy (a handful of big orders can swing a whole week), so instead of "Did we beat last week?" we ask "Was this week better than usual?" and "Was it better than the same time last year?", and we say whether the gap is just noise or something worth a look. There are a few moving parts here, so expect an intermediate workout. Have fun with it!

## Requirements

- Dashboard size: 420 x 1000 px (designed for a phone, scrolling vertically)
- 8 sheets (4 charts, 1 for the answer tiles, 1 for the header line (week and count), 2 for the KPI cards)
- Data: Sample - Superstore-2026.xlsx from the WOW data repository
- On the Data Source page, pivot Sales and Profit into a Metric / Value pair so that one set of calculations serves both metrics
- Weeks start on Sunday
- Create a parameter to select the week. Only the week starts (Sundays) of the latest 8 weeks can be selected, from 2026-06-21 to 2026-08-09. The default is the week of 2026-08-09
- Place Sales and Profit side by side in two columns, and answer two questions for each:
  - Was this week better than usual? Compare with the previous 13 weeks. This week must not be included in the average or the standard deviation
  - Was it better than the same time last year? Compare with the same 13 weeks last year: the latest 13 weeks (this week included) shifted back 52 weeks. 52 weeks is 364 days, so the weekdays line up
- Answer Yes if this week is at or above the comparison average, otherwise No
- Define the expected range as the comparison average ± 1 sample standard deviation
- In the header, show:
  - The selected week and how many questions are outside their range
  - The four Yes / No answers as 2 x 2 tiles (questions as rows, Sales and Profit as columns). Color each tile by where this week sits: above the range, at or above the average, below the average, or below the range. Add ▲ / ▼ to the answers outside the range
- In each row, add a KPI card per metric: this week's value and the $ gap from the average. Only when this week is outside the range, add how far it is above the upper bound or below the lower bound, with ▲ / ▼.
- Row 1 charts: bars for the previous 13 weeks with the range band and the average line (the Analytics pane is enough). Stop the average line before this week. Set this week's bar slightly apart and color it like the tiles
- Row 2 charts: lines for this year's latest 13 weeks and last year's same 13 weeks, with last year's average line and range band. Keep this year's line in front, and highlight this week as a circle colored like the tiles
- Below each row's charts, add a one-line, right-aligned legend for the lines, the average line and the band
- No value labels on the charts (this week's value is in the KPI cards)
- Match the formatting as closely as possible

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>With AI agents and mobile notifications, we open dashboards to go exploring less and less. I think BI is heading toward something closer to a weekly message on your phone: the answers to a few questions everyone on the team should know. If that's true, the first design decision isn't the chart type. It's which questions you answer.</p>
<p>So this week, we'll take one week of Superstore and answer four shared questions, each with a Yes / No, a number and a small chart. Weekly numbers are noisy (a handful of big orders can swing a whole week), so instead of "Did we beat last week?" we ask "Was this week better than usual?" and "Was it better than the same time last year?", and we say whether the gap is just noise or something worth a look. There are a few moving parts here, so expect an intermediate workout. Have fun with it!</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 420 x 1000 px (designed for a phone, scrolling vertically)</li>
<li>8 sheets (4 charts, 1 for the answer tiles, 1 for the header line (week and count), 2 for the KPI cards)</li>
<li>Data: Sample - Superstore-2026.xlsx from the WOW data repository</li>
<li>On the Data Source page, pivot Sales and Profit into a Metric / Value pair so that one set of calculations serves both metrics</li>
<li>Weeks start on Sunday</li>
<li>Create a parameter to select the week. Only the week starts (Sundays) of the latest 8 weeks can be selected, from 2026-06-21 to 2026-08-09. The default is the week of 2026-08-09</li>
<li>Place Sales and Profit side by side in two columns, and answer two questions for each:
<ul>
<li>Was this week better than usual? Compare with the previous 13 weeks. This week must not be included in the average or the standard deviation</li>
<li>Was it better than the same time last year? Compare with the same 13 weeks last year: the latest 13 weeks (this week included) shifted back 52 weeks. 52 weeks is 364 days, so the weekdays line up</li>
</ul>
</li>
<li>Answer Yes if this week is at or above the comparison average, otherwise No</li>
<li>Define the expected range as the comparison average ± 1 sample standard deviation</li>
<li>In the header, show:
<ul>
<li>The selected week and how many questions are outside their range</li>
<li>The four Yes / No answers as 2 x 2 tiles (questions as rows, Sales and Profit as columns). Color each tile by where this week sits: above the range, at or above the average, below the average, or below the range. Add ▲ / ▼ to the answers outside the range</li>
</ul>
</li>
<li>In each row, add a KPI card per metric: this week's value and the $ gap from the average. Only when this week is outside the range, add how far it is above the upper bound or below the lower bound, with ▲ / ▼.</li>
<li>Row 1 charts: bars for the previous 13 weeks with the range band and the average line (the Analytics pane is enough). Stop the average line before this week. Set this week's bar slightly apart and color it like the tiles</li>
<li>Row 2 charts: lines for this year's latest 13 weeks and last year's same 13 weeks, with last year's average line and range band. Keep this year's line in front, and highlight this week as a circle colored like the tiles</li>
<li>Below each row's charts, add a one-line, right-aligned legend for the lines, the average line and the band</li>
<li>No value labels on the charts (this week's value is in the KPI cards)</li>
<li>Match the formatting as closely as possible</li>
</ul>

-->
