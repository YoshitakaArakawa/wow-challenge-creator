# WOW2026 W{N}: Can You Build a Weekly Question-First Dashboard?

## Introduction

With AI agents and mobile notifications, we open dashboards to go exploring less and less. I think BI is heading toward something closer to a weekly message on your phone: the answers to a few questions everyone on the team should know. If that's true, the first design decision isn't the chart type. It's which questions you answer.

So this week, we'll take one week of Superstore and answer four shared questions, each with a Yes / No, a number and a small chart. Weekly numbers are noisy (a handful of big orders can swing a whole week), so instead of "Did we beat last week?" we ask "Was this week better than usual?" and "Was it better than the same time last year?", and we say whether the gap is just noise or something worth a look. There are a few moving parts here, so expect an intermediate workout. Have fun with it!

## Requirements

- Dashboard size: 420 x 950 px (designed for a phone, scrolling vertically)
- 6 sheets (4 charts, 1 for the answer strip, 1 for the one-line summary)
- Data: Sample - Superstore-2026.xlsx from the WOW data repository
- Weeks start on Sunday
- Create a date parameter to select the week. The default is the week of 2026-12-20
- Place Sales and Profit side by side in two columns, and answer two questions for each:
  - Was this week better than usual? Compare with the previous 13 weeks. This week must not be included in the average or the standard deviation
  - Was it better than the same time last year? Compare with the same 13 weeks last year (shifted back 52 weeks)
- Answer Yes if this week is at or above the comparison average, otherwise No
- Define the expected range as the comparison average ± 1 sample standard deviation
  - If this week is inside the range, show the gap from the average (Sales as %, Profit as a $ difference)
  - If this week is outside the range, flag it as an Alert and show how far it is above the upper bound or below the lower bound
- In the header, show all four Yes / No answers in a single row, mark the ones with an Alert, and show the number of Alerts
- Also in the header, show a one-line summary built from the answers: describe only the questions with an Alert and wrap up the rest with "Everything else is within range." If there are no Alerts, show "Everything is within range this week."
- Row 1 charts: bars for the previous 13 weeks with the range band and the average line, and this week's bar set slightly apart and highlighted
- Row 2 charts: lines for this year's latest 13 weeks and last year's same 13 weeks, with last year's average line and range band. Also show how many of this year's 13 weeks were above or below last year's range
- Highlight this week's value with color and a label in every chart
- Match the tooltips and formatting as closely as possible

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>With AI agents and mobile notifications, we open dashboards to go exploring less and less. I think BI is heading toward something closer to a weekly message on your phone: the answers to a few questions everyone on the team should know. If that's true, the first design decision isn't the chart type. It's which questions you answer.</p>
<p>So this week, we'll take one week of Superstore and answer four shared questions, each with a Yes / No, a number and a small chart. Weekly numbers are noisy (a handful of big orders can swing a whole week), so instead of "Did we beat last week?" we ask "Was this week better than usual?" and "Was it better than the same time last year?", and we say whether the gap is just noise or something worth a look. There are a few moving parts here, so expect an intermediate workout. Have fun with it!</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 420 x 950 px (designed for a phone, scrolling vertically)</li>
<li>6 sheets (4 charts, 1 for the answer strip, 1 for the one-line summary)</li>
<li>Data: Sample - Superstore-2026.xlsx from the WOW data repository</li>
<li>Weeks start on Sunday</li>
<li>Create a date parameter to select the week. The default is the week of 2026-12-20</li>
<li>Place Sales and Profit side by side in two columns, and answer two questions for each:
<ul>
<li>Was this week better than usual? Compare with the previous 13 weeks. This week must not be included in the average or the standard deviation</li>
<li>Was it better than the same time last year? Compare with the same 13 weeks last year (shifted back 52 weeks)</li>
</ul>
</li>
<li>Answer Yes if this week is at or above the comparison average, otherwise No</li>
<li>Define the expected range as the comparison average ± 1 sample standard deviation
<ul>
<li>If this week is inside the range, show the gap from the average (Sales as %, Profit as a $ difference)</li>
<li>If this week is outside the range, flag it as an Alert and show how far it is above the upper bound or below the lower bound</li>
</ul>
</li>
<li>In the header, show all four Yes / No answers in a single row, mark the ones with an Alert, and show the number of Alerts</li>
<li>Also in the header, show a one-line summary built from the answers: describe only the questions with an Alert and wrap up the rest with "Everything else is within range." If there are no Alerts, show "Everything is within range this week."</li>
<li>Row 1 charts: bars for the previous 13 weeks with the range band and the average line, and this week's bar set slightly apart and highlighted</li>
<li>Row 2 charts: lines for this year's latest 13 weeks and last year's same 13 weeks, with last year's average line and range band. Also show how many of this year's 13 weeks were above or below last year's range</li>
<li>Highlight this week's value with color and a label in every chart</li>
<li>Match the tooltips and formatting as closely as possible</li>
</ul>

-->
