# Gantt Placeholder Pattern Explained (Extreme difficulty)

A breakdown of the table-calculation chain used on the "Calendar (Extreme)" sheet of the TC26 Challenge, which **fans out concurrent sessions horizontally so they don't overlap visually**.

---

## 1. The goal

- Rows (Y): time
- Columns (X): inside each date pane, **shift overlapping sessions into lanes 0, 1, 2...**
- Marks: one vertical bar (Line mark) per session

The task is to assign each session (each `id`) an **integer horizontal offset**. That integer becomes a **placeholder continuous axis** (`2_Gantt_Placeholder_1`) placed on Columns.

## 2. Why it can't be a single formula

Tableau's calc model makes a single-expression solution essentially impossible:

| Constraint | Why it hurts |
|---|---|
| **A. Recursive running total** | "Increment every time an overlap appears" requires `PREVIOUS_VALUE` — table-calc only |
| **B. Adjacent-mark comparison** | Checking "previous session's end ≥ current session's start" needs `LOOKUP(…, -1)` |
| **C. Different addressing per sub-calc** | "Detect session boundary" and "walk along time" need different table-calc directions |

**C** is the decisive one: a single expression can only carry one addressing spec. So the logic is split into **nested table calcs**, each with its own addressing, to work around the limitation.

## 3. Mark structure (prerequisite)

- Data: `sessions` (1 row per session) joined with `minutes` (1 row per minute within a session)
- Mark LOD: **(id × minute)**
- Filtered to a single date → **Partition = Date, Addressing space = every (id, minute) mark**
- `id` sort order is fixed by a computed-sort on `0_Sorter = STR(date) + STR(start_time) + STR(duration)` = **ascending by start time**

## 4. Role of each calculation

### ① `0_Time_Axis` (dimension, row-level)
```
DATEADD('minute', [Minute], [start_time])
```
Session start + elapsed minutes timestamp. The foundation value later `LOOKUP`-ed by downstream table calcs.

---

### ② `0_INDEX = INDEX()`
- **Addressing: `id` only** (partition = time)
- **Purpose**: within each time slice, number the sessions active at that moment as 1, 2, 3... in id order. Only the session with the earliest start time gets `② = 1`.

---

### ③ `0_Is_Gantt_Start = INDEX() = 1`
- **Addressing: `0_Time_Axis` only** (partition = id)
- **Purpose**: flags "the first minute of this session" as TRUE. Walking time within each id makes `INDEX() = 1` fire on `minute = 0` = **session start**.

② and ③ have **orthogonal addressing**. ② is "fix time, scan across id"; ③ is "fix id, scan across time". Combined, they pinpoint the single first mark of the whole partition.

---

### ④ `0_Is_Gantt_Start_Overlap`
```
MIN([0_Time_Axis]) <= LOOKUP(MIN([0_Time_Axis]), -1)
```
- **Addressing: `id` → `0_Time_Axis`** (both, in that order)
- **Purpose**: "did the time axis go backwards or stall vs. the previous mark?" = **overlap detector between sessions**.

With (id, time) addressing, marks are flattened into this sequence:

```
A min0, A min1, ..., A minN, B min0, B min1, ..., B minM, C min0, ...
```

- Inside one id: time increases by +1 minute → FALSE
- At an id boundary (A's last → B's first): if B's start ≤ A's end → TRUE = **B overlaps A**

Uses `LOOKUP`, so it can't be row-level — must be a table calc.

---

### ⑤ `1_Delta_1 = IF ④ THEN 1 ELSE 0`
- **Addressing: Table (across) / Rows** (irrelevant in practice — the nested ④'s addressing governs)
- **Purpose**: bool → numeric bridge. Split out for **readability and reuse**: if you ever want a non-unit increment, you only touch this step.

---

### ⑥ `2_Gantt_Placeholder_1`
```
IF [0_Is_Gantt_Start] AND [0_INDEX] = 1
THEN 0
ELSE [1_Delta_1] + PREVIOUS_VALUE(0)
END
```
- **Addressing: `id` → `0_Time_Axis`** (partition = Date)
- **Purpose**: the recursive running total itself.
  - First mark: initialize to 0
  - Otherwise: **previous mark's value + (1 if overlap, 0 otherwise)**

The init condition `③ AND ② = 1` = "first minute of the first session" = the single mark that's true in the whole partition — the recursion seed.

## 5. Execution trace

Example: A (9:00–10:00), B (9:30–10:30), C (11:00–12:00), D (11:15–12:15)

| Mark | ④ | ⑤ | ⑥ (offset) |
|---|---|---|---|
| A min0 (first) | — | — | **0** (init) |
| A min1..60 | FALSE | 0 | 0 |
| B min0 (overlaps A) | TRUE | 1 | 0 + 1 = **1** |
| B min1..60 | FALSE | 0 | 1 |
| C min0 (no overlap with B) | FALSE | 0 | 1 |
| C min1..60 | FALSE | 0 | 1 |
| D min0 (overlaps C) | TRUE | 1 | 1 + 1 = **2** |
| D min1..60 | FALSE | 0 | 2 |

**All marks within a single session share the same X coordinate**, so each session draws as a straight vertical line; only overlapping sessions shift right.

## 6. Settings in the table-calc dialog

Select ⑥ → Edit Table Calculation → the nested structure:

```
2_Gantt_Placeholder_1
├── Compute using: Specific Dimensions
│     Order: id → 0_Time_Axis (both Field order)
│
├─[nested] 0_Is_Gantt_Start          → 0_Time_Axis only
├─[nested] 0_INDEX                   → id only
├─[nested] 1_Delta_1                 → Table (across)
└─[nested] 0_Is_Gantt_Start_Overlap  → id → 0_Time_Axis
```

**Switching addressing per nested level is the heart of this pattern.** If every nested calc shared the same addressing, ③'s `INDEX() = 1` would only fire on the single first mark in the partition instead of each session's start — breaking the init logic.

## 7. Finishing touches on the view

- **Columns**: `ATTR([Date]) * 2_Gantt_Placeholder_1` — date slices the panes, the placeholder spreads overlapping sessions horizontally within each pane
- **Rows**: `0_Time_Axis` (continuous, `reverse=true` so time flows top→bottom)
- **Marks**: Line, Detail = `id`, Color = `ATTR(AI Session Flag)`
- Placeholder axis hidden with `display=false`; `range-type=independent` keeps per-date widths stable
- `mark-transparency=180`, small Size → thin vertical bars that read as Gantt segments

## 8. Why six calcs? (recap)

1. Row-level can't do this (`LOOKUP` / `PREVIOUS_VALUE` needed) → must be table calcs
2. Recursion needs both "per-step delta" and "init condition" → split into delta side (④⑤) and init side (②③)
3. Init condition requires "session start" AND "partition start" judged simultaneously — former needs time addressing, latter needs id addressing → ② and ③ separated
4. Delta detection needs to look at adjacent id boundaries → ④ is its own calc
5. ⑤ is a thin readability wrapper
6. ⑥ consolidates everything into the recursive total

The pattern's essence: Tableau only lets one expression carry one addressing spec, so you **decompose into nested calcs and give each nest its own addressing** to route around that constraint.
