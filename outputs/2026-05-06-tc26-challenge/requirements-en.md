# WOW2026 W18: Can You Spot the AI Wave at TC26?

## Introduction

This challenge was released at the TC26 Workout Wednesday session. 
Whether you're here in the room or finding it later, I hope you'll have fun!

In this challenge, we'll visualize the sessions of Tableau Conference itself. Three difficulty tiers are available, so pick the one that matches your confidence and give it a try. Let's dive right in!

## Requirements

- Dashboard size: 1000 x 800
- Use the provided `sessions.csv` dataset
- Flag a session as AI-related when any of the following match:
    - Title contains `AI` or `Agent`
    - Topic is `Agentic Analytics` or `Artificial Intelligence`
- Display a BAN showing the share of TC26 sessions that are AI-related
- Build a calendar:
    - Vertical axis: session start time
    - Within the same start time, place AI-related sessions on the left

### Bonus

- Recalculate the BAN using total session duration in minutes instead of session count
- Size each circle by its session duration
- Within each day's start-time row, sort circles by duration, resetting the order between the AI-related group and the non-AI group
- In the tooltip, color the session title to match its circle color (AI-related vs. non-AI)

### Extreme

- Filter the data to May 5 sessions only
- Build the calendar as a space-efficient Gantt chart:
    - Vertical axis: time of day
    - Each session: a vertical line from its start to its end time
- Stack overlapping sessions in adjacent columns:
    - When sessions overlap, place them side-by-side in the next column to the right
    - When the overlap chain breaks, snap the next session back to the leftmost column
- Hint:
    - Combine the provided `minutes.csv` with the sessions for data densification
    - Overlap is defined as: current session's start time ≤ previous session's end time
    - You'll need nested table calculations and `PREVIOUS_VALUE()`
    - For the full algorithm, see the "Simple Stacking with Reset" section at [Space-Effective Gantt Chart](https://www.yarakawa.com/single-post/space_effective_gantt_chart)

<!-- HTML VERSION (for site posting)

<h2>Introduction</h2>
<p>This challenge was released at the TC26 Workout Wednesday session. Whether you're here in the room or finding it later, jump in and have fun.</p>
<p>In this challenge, we'll visualize the sessions of Tableau Conference itself. Three difficulty tiers are available, so pick the one that matches your confidence and give it a try. Let's dive right in!</p>

<h2>Requirements</h2>
<ul>
<li>Dashboard size: 1000 x 800</li>
<li>Use the provided sessions.csv dataset</li>
<li>Flag a session as AI-related when any of the following match:
  <ul>
    <li>Title contains AI or Agent</li>
    <li>Topic is Agentic Analytics or Artificial Intelligence</li>
  </ul>
</li>
<li>Display a BAN showing the share of TC26 sessions that are AI-related</li>
<li>Build a calendar:
  <ul>
    <li>Vertical axis: session start time</li>
    <li>Within the same start time, place AI-related sessions on the left</li>
  </ul>
</li>
</ul>

<h3>Bonus</h3>
<ul>
<li>Recalculate the BAN using total session duration in minutes instead of session count</li>
<li>Size each circle by its session duration</li>
<li>Within each day's start-time row, sort circles by duration, resetting the order between the AI-related group and the non-AI group</li>
<li>In the tooltip, color the session title to match its circle color (AI-related vs. non-AI)</li>
</ul>

<h3>Extreme</h3>
<ul>
<li>Filter the data to May 5 sessions only</li>
<li>Build the calendar as a space-efficient Gantt chart:
  <ul>
    <li>Vertical axis: time of day</li>
    <li>Each session: a vertical line from its start to its end time</li>
  </ul>
</li>
<li>Stack overlapping sessions in adjacent columns:
  <ul>
    <li>When sessions overlap, place them side-by-side in the next column to the right</li>
    <li>When the overlap chain breaks, snap the next session back to the leftmost column</li>
  </ul>
</li>
<li>Hint:
  <ul>
    <li>Combine the provided minutes.csv with the sessions for data densification</li>
    <li>Overlap is defined as: current session's start time ≤ previous session's end time</li>
    <li>You'll need nested table calculations and PREVIOUS_VALUE()</li>
    <li>For the full algorithm, see the "Simple Stacking with Reset" section at <a href="https://www.yarakawa.com/single-post/space_effective_gantt_chart">Space-Effective Gantt Chart</a></li>
  </ul>
</li>
</ul>

-->
