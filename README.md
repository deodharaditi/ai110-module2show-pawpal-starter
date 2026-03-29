# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond the greedy time-budget scheduler, PawPal+ includes four algorithmic improvements:

- **Sort by time** — `Scheduler.sort_by_time()` orders any task list chronologically using the `preferred_time` ("HH:MM") field. Tasks with no preferred time sort to the end. Zero-padded strings sort correctly as plain strings, so no time parsing is needed.
- **Filter by pet or status** — `Owner.get_tasks_for_pet(name)` returns pending tasks for one pet by name; `Owner.get_tasks_by_status(completed)` returns all tasks across all pets matching a completion state.
- **Recurring tasks** — `Pet.complete_task(title)` marks a task done and, for `daily` or `weekly` tasks, automatically appends a fresh copy with `due_date` set to tomorrow or next week using `timedelta`. `get_pending_tasks()` filters by `due_date <= today` so future occurrences stay hidden until they are due.
- **Conflict detection** — `Scheduler.detect_conflicts()` groups scheduled tasks by `preferred_time` using a `defaultdict` and returns a warning string for any slot claimed by more than one task. Warnings appear in the plan summary under a WARNINGS section.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
