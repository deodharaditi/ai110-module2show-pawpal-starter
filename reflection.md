# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions the system supports are: entering owner and pet info, adding and editing care tasks, and generating a daily plan with reasoning.

To support these, the initial UML design uses five classes:

**Owner** is the entry point for the system. It holds the owner's `name` and `time_available_per_day` (in minutes), which is the primary constraint the scheduler works within. Its `get_constraints()` method packages that budget into a form the `Scheduler` can consume. `Owner` also holds a reference to its `Pet`.

**Pet** captures the animal's identity and health context: `name`, `species`, `age`, and `health_notes`. It is a passive data object — the `Scheduler` and `Owner` read from it but it does not drive any logic itself. `get_info()` returns a readable summary for display purposes.

**Task** is the central unit of work. Each task has a `title`, `task_type` (e.g. walk, feed, meds, grooming, enrichment), `duration_minutes`, `priority` (high/medium/low), an `is_required` flag for non-negotiable tasks, and optional `notes`. `is_feasible(available_minutes)` lets the scheduler quickly check if a task fits in the remaining time budget. `to_dict()` serializes the task for display in the Streamlit UI.

**Scheduler** is the only class with real logic. It holds references to `Owner`, `Pet`, and the full list of `Task` objects. Its responsibilities are separated into: `filter_tasks()` (drop tasks that exceed remaining time), `rank_tasks()` (sort by priority and required status), `explain()` (produce per-task reasoning strings), and `generate_plan()` which orchestrates all three and returns a `DailyPlan`.

**DailyPlan** is the output object. It stores the list of `scheduled_tasks`, the `unscheduled_tasks` that didn't fit, the `total_duration` of the plan, and a `reasoning` dict mapping each task title to a short explanation of why it was included or excluded. `get_summary()` returns a human-readable overview for the UI.

**b. Design changes**

Three changes were made to the initial skeleton based on design review:

1. **Removed `pet` from `Scheduler.__init__`** — The original skeleton passed both `owner` and `pet` as separate arguments to `Scheduler`, but `Owner` already holds a `pet` reference. Having two separate paths to the same object creates a risk of them falling out of sync. The scheduler now accesses the pet via `self.owner.pet`, making `Owner` the single source of truth.

2. **Renamed `explain()` to `_explain()`** — `explain()` was designed to produce the reasoning dict that `DailyPlan.reasoning` needs. If it stays public, callers might invoke it independently and get confused about when it should be called relative to `generate_plan()`. Marking it private (`_explain()`) signals that it is an internal step called by `generate_plan()`, not a standalone operation.

3. **Replaced `priority: str` with `priority: Priority` (Enum)** — Storing priority as a free-form string means `rank_tasks()` would have to compare strings like `"high"` and `"medium"`. A typo or inconsistent casing would silently break ordering. A `Priority` enum with values `HIGH`, `MEDIUM`, and `LOW` makes invalid priorities a hard error at assignment time and makes comparisons unambiguous.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: total time budget (owner's `time_available_per_day`), task priority (HIGH/MEDIUM/LOW via the `Priority` enum), and a required flag (`is_required`) for non-negotiable tasks. Time budget is the hard outer limit — no task is added once minutes run out. Within that limit, required tasks always come before optional ones, and ties are broken by priority descending. Preferred time (`preferred_time`) is a soft preference used only for display ordering and conflict detection, not for inclusion decisions. Time budget mattered most because it is the one constraint that is objectively non-negotiable: you cannot schedule more care than you have hours for.

**b. Tradeoffs**

The conflict detector uses exact `preferred_time` string matching rather than checking overlapping time windows. For example, a 30-minute task at `08:00` and a 5-minute task at `08:15` overlap by 15 minutes in real life, but the scheduler does not flag them — only two tasks sharing the exact string `"08:15"` would trigger a warning.

This tradeoff is reasonable for this scenario because the app targets casual pet owners who set approximate time preferences, not a rigid minute-by-minute calendar. Checking for exact collisions catches the most obvious double-bookings (two feedings at `07:30`, for instance) without requiring precise start/end times for every task. A duration-aware overlap check would be more accurate but would also require the app to track actual start times, adding complexity that does not match the app's informal scheduling model.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase of the project, but the role shifted depending on the phase. During design, it was a brainstorming partner — asked to identify what classes were needed, what methods each should expose, and where responsibilities could become tangled. During implementation, it generated first drafts of methods like `complete_task()` and `detect_conflicts()` that I then read carefully before accepting. During testing, it proposed a test plan covering happy paths and edge cases, then wrote the actual test functions. During documentation, it drafted docstrings and README sections from the existing code.

The most effective prompts were narrow and specific rather than open-ended. Asking "write a method that marks a task complete and appends a next occurrence for daily or weekly frequency using timedelta" produced immediately usable code. Asking "how should I design the scheduler?" produced a wall of generic advice. Framing questions around a concrete constraint ("the Scheduler should only take owner as an argument — how do I access the pet from there?") consistently returned more useful output than asking for high-level opinions.

**b. Judgment and verification**

The clearest rejection was the original `Scheduler.__init__` skeleton, which took both `owner` and `pet` as separate constructor arguments. The AI generated this because both objects are logically relevant to the scheduler, and it is a natural first instinct to pass everything a class needs directly into its constructor. However, `Owner` already holds a reference to `Pet` — passing `pet` separately creates two independent paths to the same object, which means they can silently fall out of sync if one is updated and the other is not.

The fix was to remove the `pet` parameter entirely and have `Scheduler` access the pet via `self.owner.pets`. This was verified by checking: if `Owner` is the single source of truth, no other object should hold a separate reference to the same data. The AI accepted the correction immediately when the reasoning was stated explicitly, which confirmed the original suggestion was a default pattern rather than a considered design choice.

A second modification: when asked for a "Pythonic" simplification of `filter_tasks()`, the AI suggested replacing the explicit `remaining` loop with `itertools.accumulate`. The accumulate version was shorter but required a reader to mentally simulate two parallel lists to understand what was happening. The explicit loop makes the budget deduction visible on every iteration — which is the point of the function. I kept the original. Shorter is not always clearer, and clarity matters more in code that encodes a business rule.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers four behavioral areas: core task operations (`mark_complete`, `add_task`), sorting correctness (chronological order, untimed tasks last, no crash on all-untimed input), recurrence logic (daily → tomorrow, weekly → +7 days, as-needed → no recurrence, missing title → no crash), and conflict detection (same slot triggers warning, different slots return empty, no preferred time is never flagged). Edge cases include an empty pet task list, a task with a future `due_date` that should be excluded from pending, an unknown pet name returning `[]`, and a zero time budget that skips every task.

These tests mattered because the scheduling algorithm is invisible in the UI — a user just sees the final plan. Without unit tests there is no way to verify that the greedy filter, recurrence logic, and conflict detection behave correctly for inputs that the manual demo does not exercise.

**b. Confidence**

Confidence level: 4 out of 5. All 16 tests pass and cover the core decision points. The remaining gap is integration coverage: there are no automated tests for the Streamlit session state flow, and `generate_plan()` is tested implicitly through its components but not as a full end-to-end call with multiple pets, a tight budget, and overlapping required tasks. That scenario would be the next test to write.

---

## 5. Reflection

**a. What went well**

The class boundary decisions held up well throughout the build. Keeping `Scheduler` focused on scheduling logic (ranking, filtering, sorting, conflict detection) and pushing all data mutation into `Pet` and `Owner` meant that adding new features — recurring tasks, conflict detection, sort by time — never required touching classes that were already working. Each addition slotted into the existing structure without breaking anything else.

**b. What you would improve**

The conflict detector uses exact time-string matching. A more useful version would convert `preferred_time` + `duration_minutes` into a real time interval and flag any two tasks whose intervals overlap. This would catch cases like a 30-minute task at `08:00` overlapping with a task at `08:15` — a real conflict that the current detector silently misses. The change would require storing start times more carefully but would make the warnings genuinely reliable rather than approximate.

**c. Key takeaway**

The most important thing learned was that AI collaboration works best when the human holds the design constraints and the AI generates within them — not the other way around. Every time a suggestion was accepted without checking it against the design (does this create a duplicate reference? does this make the method public when it should be private?), a correction was needed later. Every time a constraint was stated explicitly before asking for code, the output was usable with minimal modification. The lead architect role is not about writing every line — it is about knowing which questions to ask, which suggestions to scrutinize, and which design rules are non-negotiable.

---

## 6. Prompt Comparison (Challenge 5)

**Task used for comparison:** Implement the logic for rescheduling a weekly recurring task when it is marked complete — specifically, the method that marks the task done and queues a new occurrence due in exactly one week, without duplicating the original task's metadata.

**Prompt sent to both models:**
> "In a Python dataclass-based pet care scheduler, I have a `Pet` class that holds a list of `Task` objects. Each task has a `frequency` field ('daily', 'weekly', or 'as-needed'), a `completed` bool, and a `due_date` field. Write a `complete_task(title)` method on `Pet` that marks the matching task done, and if the frequency is 'daily' or 'weekly', appends a new copy of that task with `completed=False` and `due_date` set to tomorrow or next week. The Task is a dataclass — use the most idiomatic Python approach to copy it with modified fields."

---

**GPT-4o response (summary):**

GPT-4o produced a working solution but reached for `copy.deepcopy()` to clone the task before modifying fields:

```python
import copy

def complete_task(self, title: str):
    for task in self.tasks:
        if task.title == title and not task.completed:
            task.completed = True
            if task.frequency == "daily":
                new_task = copy.deepcopy(task)
                new_task.completed = False
                new_task.due_date = date.today() + timedelta(days=1)
                self.tasks.append(new_task)
            elif task.frequency == "weekly":
                new_task = copy.deepcopy(task)
                new_task.completed = False
                new_task.due_date = date.today() + timedelta(weeks=1)
                self.tasks.append(new_task)
            return
```

This works correctly but has two issues: `deepcopy` is heavier than needed for a flat dataclass with no nested mutable state, and the `if/elif` blocks for daily/weekly are nearly identical — the recurrence delta is the only difference, so the branching can be collapsed into a lookup.

---

**Claude (this project) response (summary):**

The version used in this project uses `dataclasses.replace()` and a dict lookup for the recurrence delta:

```python
from dataclasses import replace

def complete_task(self, title: str):
    task = next((t for t in self.tasks if t.title == title and not t.completed), None)
    if not task:
        return
    task.mark_complete()
    recurrence = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
    delta = recurrence.get(task.frequency)
    if delta:
        self.tasks.append(replace(task, completed=False, due_date=date.today() + delta))
```

---

**Comparison:**

| Dimension | GPT-4o | Claude |
|---|---|---|
| Copy mechanism | `copy.deepcopy()` | `dataclasses.replace()` |
| Recurrence branching | `if/elif` per frequency | dict lookup, single `replace()` call |
| Lines of logic | ~12 | ~6 |
| Dataclass idioms | Partial (no `replace`) | Full (`replace` is the stdlib tool for this) |
| as-needed handled | No (silently ignored) | Yes (dict miss returns `None`, no branch needed) |

**Winner: Claude** — for two reasons. First, `dataclasses.replace()` is the purpose-built stdlib function for copying a dataclass with field overrides. Using `deepcopy` signals unfamiliarity with the dataclass API. Second, the dict lookup for recurrence deltas eliminates duplicate branches and automatically handles the `as-needed` case: `recurrence.get("as-needed")` returns `None`, so the `if delta` guard skips appending without any extra branch. GPT-4o's version silently ignores `as-needed` by not having an `elif` for it — which happens to be correct behavior, but for the wrong reason. The dict approach makes the intent explicit.

**What this comparison revealed about prompting:** Both models needed the constraint stated explicitly ("Task is a dataclass — use the most idiomatic Python approach") to avoid a generic solution. Without that phrase, early drafts from both models used plain attribute assignment on a manually constructed `Task(...)` call, duplicating every field. The idiomatic direction in the prompt is what pushed Claude toward `replace()` and GPT-4o toward `deepcopy` — a meaningful difference in how each model interprets "idiomatic."
