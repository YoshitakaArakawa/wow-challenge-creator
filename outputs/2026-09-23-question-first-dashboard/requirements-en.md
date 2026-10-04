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
  - Color by where this week sits, in four levels:
    - Above the range
    - Inside the range, at or above the average
    - Inside the range, below the average
    - Below the range
  - Add ▲ / ▼ to the answers outside the range
- Elements to show:
  - Header
    - The four answers as tiles
    - This week's value for each metric
  - KPI cards (per question and metric)
    - The $ gap from the average, and the average itself
    - When outside the range, also how far this week is past the bound
  - Chart for "better than usual?"
    - Bars for the weekly values of the previous 13 weeks and this week
    - The range and average of the comparison period. Keep them off this week's bar
  - Chart for "better than the same time last year?"
    - Lines for the weekly values of this year's 13 weeks and last year's 13 weeks
    - Last year's range and average
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
<li>Color by where this week sits, in four levels:
<ul>
<li>Above the range</li>
<li>Inside the range, at or above the average</li>
<li>Inside the range, below the average</li>
<li>Below the range</li>
</ul>
</li>
<li>Add ▲ / ▼ to the answers outside the range</li>
</ul>
</li>
<li>Elements to show:
<ul>
<li>Header
<ul>
<li>The four answers as tiles</li>
<li>This week's value for each metric</li>
</ul>
</li>
<li>KPI cards (per question and metric)
<ul>
<li>The $ gap from the average, and the average itself</li>
<li>When outside the range, also how far this week is past the bound</li>
</ul>
</li>
<li>Chart for "better than usual?"
<ul>
<li>Bars for the weekly values of the previous 13 weeks and this week</li>
<li>The range and average of the comparison period. Keep them off this week's bar</li>
</ul>
</li>
<li>Chart for "better than the same time last year?"
<ul>
<li>Lines for the weekly values of this year's 13 weeks and last year's 13 weeks</li>
<li>Last year's range and average</li>
</ul>
</li>
</ul>
</li>
<li>Match the formatting as closely as possible</li>
</ul>

-->
