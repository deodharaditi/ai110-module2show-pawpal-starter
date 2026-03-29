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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
