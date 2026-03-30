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

## Scheduling tradeoffs

Conflict detection uses **exact time-string matching**, not duration-aware window overlap. A 30-minute task at `08:00` and a 5-minute task at `08:15` overlap in reality but are not flagged — only two tasks sharing the identical string `"08:15"` trigger a warning. This is intentional: the app targets casual owners who set approximate time preferences, not a rigid calendar, so lightweight collision detection covers the most useful cases without requiring precise start/end tracking for every task.
