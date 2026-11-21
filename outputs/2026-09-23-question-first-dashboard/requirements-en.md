# WOW2026 W40: Can You Build a Weekly Check-In Dashboard?

## Introduction

Did you watch the Tableau keynote at Dreamforce 2026? I enjoyed it, and there were a lot of big announcements. It also left me thinking about where dashboards fit now. Ad hoc analysis seems to be moving to AI, and we're somewhere in the middle of that shift. My current view is that dashboards are for delivering the right information at the right time. For some dashboards, that means answering the few questions everyone on the team should know.

In this challenge, you'll build one of those. It gives four Yes / No answers, each with a number and a small chart. Weekly numbers can be noisy, so each answer is checked against a normal range instead of just last week. Have fun with it!

## Requirements

- Dashboard size: 420 x 1000 px (designed for a phone, scrolling vertically)
- Create a parameter to select a week. The choices are the 8 week starts (Sundays) from 2026-06-21 to 2026-08-09, and the default is 2026-08-09. Below, "this week" means the selected week
- Answer two questions for Sales and for Profit:
  - Was this week better than usual? Compare with the 13 weeks before this week
  - Was it better than the same time last year? Compare with the 13 weeks ending with this week, shifted back 52 weeks (364 days, so the weekdays line up)
- For each comparison:
  - Answer Yes if this week is at or above the comparison average, otherwise No
  - The range is the average ± 1 sample standard deviation. Values on the bounds count as inside
  - Color by where this week sits, and add ▲ / ▼ to the answers outside the range:
    - Above the range: dark blue (#2063b0)
    - Inside the range, at or above the average: light blue (#a6c0e1)
    - Inside the range, below the average: light red (#e4a59f)
    - Below the range: dark red (#a83634)
- Header: the four answers as tiles, with this week's value for each metric
- KPI cards: the $ gap from the average and the average itself, plus how far this week is past the bound when outside the range
- Bar chart (better than usual?): the previous 13 weeks and this week, with the range and average kept off this week's bar
- Line chart (same time last year?): this year's and last year's 13 weeks, with last year's range and average
- Match the formatting as closely as possible

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>Did you watch the Tableau keynote at Dreamforce 2026? I enjoyed it, and there were a lot of big announcements. It also left me thinking about where dashboards fit now. Ad hoc analysis seems to be moving to AI, and we're somewhere in the middle of that shift. My current view is that dashboards are for delivering the right information at the right time. For some dashboards, that means answering the few questions everyone on the team should know.</p>
<p>In this challenge, you'll build one of those. It gives four Yes / No answers, each with a number and a small chart. Weekly numbers can be noisy, so each answer is checked against a normal range instead of just last week. Have fun with it!</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 420 x 1000 px (designed for a phone, scrolling vertically)</li>
<li>Create a parameter to select a week. The choices are the 8 week starts (Sundays) from 2026-06-21 to 2026-08-09, and the default is 2026-08-09. Below, "this week" means the selected week</li>
<li>Answer two questions for Sales and for Profit:
<ul>
<li>Was this week better than usual? Compare with the 13 weeks before this week</li>
<li>Was it better than the same time last year? Compare with the 13 weeks ending with this week, shifted back 52 weeks (364 days, so the weekdays line up)</li>
</ul>
</li>
<li>For each comparison:
<ul>
<li>Answer Yes if this week is at or above the comparison average, otherwise No</li>
<li>The range is the average ± 1 sample standard deviation. Values on the bounds count as inside</li>
<li>Color by where this week sits, and add ▲ / ▼ to the answers outside the range:
<ul>
<li>Above the range: dark blue (#2063b0)</li>
<li>Inside the range, at or above the average: light blue (#a6c0e1)</li>
<li>Inside the range, below the average: light red (#e4a59f)</li>
<li>Below the range: dark red (#a83634)</li>
</ul>
</li>
</ul>
</li>
<li>Header: the four answers as tiles, with this week's value for each metric</li>
<li>KPI cards: the $ gap from the average and the average itself, plus how far this week is past the bound when outside the range</li>
<li>Bar chart (better than usual?): the previous 13 weeks and this week, with the range and average kept off this week's bar</li>
<li>Line chart (same time last year?): this year's and last year's 13 weeks, with last year's range and average</li>
<li>Match the formatting as closely as possible</li>
</ul>

-->
