# PawPal+ Project Reflection

## 1. System Design

**a. Core user actions**

The three core actions a user should be able to perform in PawPal+ are:

1. **Enter owner and pet information** — The user provides basic details about themselves (e.g., name, time available per day) and their pet (e.g., name, species, age). This context shapes what kinds of tasks are relevant and how much can realistically be scheduled in a day.

2. **Add and edit pet care tasks** — The user creates tasks such as walks, feeding, medication, enrichment, and grooming. Each task has at minimum a duration (how long it takes) and a priority (how important it is). The user can also edit or remove tasks as their pet's needs change over time.

3. **Generate and view a daily care plan** — The user requests a daily schedule, and the app produces an ordered plan that fits within the owner's available time, respects task priorities, and explains why certain tasks were included or excluded. The user can review the plan and understand the reasoning behind it.

**b. Initial design**

The system is built around five main objects:

**Owner**
- Holds: `name` (str), `time_available_per_day` (int, minutes)
- Can: `get_constraints()` — returns the owner's time budget and preferences so the scheduler knows what it is working within

**Pet**
- Holds: `name` (str), `species` (str), `age` (int), `health_notes` (str)
- Can: `get_info()` — returns a summary of pet details that inform which tasks are relevant or urgent

**Task**
- Holds: `title` (str), `task_type` (str — e.g. walk, feed, meds, grooming, enrichment), `duration_minutes` (int), `priority` (str — high/medium/low), `is_required` (bool), `notes` (str)
- Can: `is_feasible(available_minutes)` — checks whether the task fits in the remaining daily time budget; `to_dict()` — serializes the task for display or storage

**Scheduler**
- Holds: `owner` (Owner), `pet` (Pet), `tasks` (list of Task)
- Can: `generate_plan()` — orchestrates filtering, ranking, and assembly of a DailyPlan; `filter_tasks()` — removes tasks that exceed available time; `rank_tasks()` — orders tasks by priority; `explain()` — produces human-readable reasoning for each scheduling decision

**DailyPlan**
- Holds: `scheduled_tasks` (list of Task), `unscheduled_tasks` (list of Task), `total_duration` (int), `reasoning` (dict mapping task title to explanation string)
- Can: `get_summary()` — returns a readable overview of what is planned, what was left out, and why

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
