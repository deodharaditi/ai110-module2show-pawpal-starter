# PawPal+ — Pet Care Scheduling Assistant

PawPal+ is a Streamlit app that helps a busy pet owner stay consistent with daily pet care. Enter your pets and tasks, set a time budget, and let the scheduler build a prioritized plan — complete with conflict warnings and recurring task support.

## 📸 Demo

> _Add a screenshot of your running Streamlit app here._
> `![PawPal+ Demo](demo_screenshot.png)`

---

## Features

### Core scheduling
- **Priority-based greedy scheduler** — required tasks are always scheduled first; within the same required status, tasks are ordered HIGH → MEDIUM → LOW priority. Tasks that exceed the remaining time budget are skipped and surfaced as "skipped — no time remaining."
- **Time budget progress bar** — visual indicator shows minutes used vs. available so owners can see at a glance how full their day is.

### Weighted scoring (Challenge 1 — Agent Mode)
- **`Scheduler.score_task(task, budget)`** — assigns each task a numeric score combining three factors: priority rank (HIGH=3, MEDIUM=2, LOW=1), a +10 required bonus so required tasks always outrank optional ones, and an efficiency ratio (`priority_rank / (duration_minutes / budget)`). A short HIGH task scores higher than a long HIGH task when the budget is tight, so it is scheduled first — leaving room for more tasks overall.
- **`Scheduler.rank_tasks_weighted(tasks, budget)`** — sorts by `score_task()` descending. Used by `generate_plan(weighted=True)` (the default).
- **`generate_plan(weighted=True/False)`** — pass `weighted=False` to fall back to simple priority order; the default uses weighted scoring.

### Smarter algorithms
- **Sort by preferred time** — any task list can be ordered chronologically by `preferred_time` (HH:MM). Tasks with no preferred time sink to the end. Zero-padded strings sort correctly as plain strings — no time parsing needed.
- **Filter by pet or completion status** — view pending tasks for a single pet or filter across all pets by done/not-done status.
- **Recurring task support** — marking a `daily` or `weekly` task complete automatically queues the next occurrence with the correct `due_date` (tomorrow or +7 days via `timedelta`). Future occurrences stay hidden until they are due.
- **Conflict detection** — the scheduler groups scheduled tasks by `preferred_time` and flags any slot shared by more than one task. Warnings appear prominently above the schedule with a tip to adjust the conflicting task's time.

### System design
- Five-class architecture: `Priority` (enum), `Task`, `Pet`, `Owner`, `Scheduler`, `DailyPlan`
- `Owner` is the single source of truth — `Scheduler` accesses pets and tasks through `Owner`, eliminating duplicate references
- `Task` uses a `Priority` enum (not a raw string) so invalid priorities are a hard error at assignment time

---

## Project structure

```
pawpal_system.py   # Core business logic (all classes)
app.py             # Streamlit UI
main.py            # Terminal demo / manual testing ground
tests/
  test_pawpal.py   # 16 automated pytest tests
reflection.md      # Design decisions and tradeoffs
uml_final.png      # Final class diagram
```

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the terminal demo

```bash
python main.py
```

---

## Testing PawPal+

```bash
python -m pytest tests/test_pawpal.py -v
```

16 tests covering:

| Area | What is tested |
|---|---|
| Core task behavior | `mark_complete()`, `add_task()` |
| Sorting | Chronological order, untimed tasks last, no crash on empty times |
| Recurrence | Daily → tomorrow, weekly → +7 days, as-needed → no recurrence, missing title → no crash |
| Conflict detection | Same slot → warning, different slots → empty, no preferred time → ignored |
| Edge cases | Empty pet, future `due_date` excluded, unknown pet name, zero time budget |

**Confidence level: 4 / 5** — core scheduling logic is fully unit-tested. Gap: no automated tests for the Streamlit UI or the full `generate_plan()` end-to-end pipeline.

---

## Agent Mode — how it was used (Challenge 1)

The weighted scoring feature was designed and implemented using Claude Code in Agent Mode. Rather than asking for a complete solution, Agent Mode was used in focused steps that mirror how a lead architect would delegate to a capable collaborator:

1. **Design prompt** — "Propose a scoring formula for pet care tasks that rewards high priority and penalizes long duration relative to the available budget." Agent Mode returned the `required_bonus + (priority_rank / duration_fraction)` formula with a clear explanation of why each term was included.

2. **Boundary check** — Before accepting the formula, the edge case of `budget=0` was raised. Agent Mode updated `score_task()` to guard against division by zero by defaulting `duration_fraction` to 1 when budget is zero.

3. **Test generation** — "Write four pytest tests for `score_task` and `rank_tasks_weighted` covering: required vs optional at same priority, shorter vs longer at same priority, ordering, and an end-to-end plan comparison." One test had a logic error (comparing required LOW vs optional HIGH — not actually the same priority) which the test run caught immediately. Agent Mode identified the test was wrong, not the implementation, and fixed the assertion.

4. **Documentation** — Agent Mode drafted the docstrings for `score_task` and `rank_tasks_weighted`, including the worked example in the `score_task` docstring showing how a 5-min task scores higher than a 50-min task at the same priority.

**What Agent Mode added:** the ability to reason about the scoring formula mathematically before writing code, and to catch the test logic error by reading the failure message and tracing it back to the test's own assumptions rather than blaming the implementation.

## Scheduling tradeoffs

Conflict detection uses **exact time-string matching**, not duration-aware window overlap. A 30-minute task at `08:00` and a 5-minute task at `08:15` overlap in reality but are not flagged — only two tasks sharing the identical string `"08:15"` trigger a warning. This is intentional: the app targets casual owners who set approximate time preferences, not a rigid calendar, so lightweight collision detection covers the most useful cases without requiring precise start/end tracking for every task.
