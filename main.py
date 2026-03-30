import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import date
from tabulate import tabulate
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

TASK_TYPE_EMOJI = {
    "walk": "🦮", "feed": "🍖", "meds": "💊",
    "grooming": "✂️", "enrichment": "🎾", "general": "📋",
}
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}

# --- Setup ---
mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

mochi.add_task(Task(title="Evening walk",     task_type="walk",       duration_minutes=25, priority=Priority.MEDIUM, preferred_time="18:00"))
mochi.add_task(Task(title="Breakfast",        task_type="feed",       duration_minutes=10, priority=Priority.HIGH,   is_required=True,  preferred_time="07:30"))
mochi.add_task(Task(title="Morning walk",     task_type="walk",       duration_minutes=30, priority=Priority.HIGH,   is_required=True,  preferred_time="08:00"))
mochi.add_task(Task(title="Fetch in the yard",task_type="enrichment", duration_minutes=20, priority=Priority.MEDIUM, preferred_time="15:00"))

luna.add_task(Task(title="Medication",    task_type="meds",     duration_minutes=5,  priority=Priority.HIGH,   is_required=True, preferred_time="08:15", notes="Half a tablet with food"))
luna.add_task(Task(title="Brush coat",   task_type="grooming",  duration_minutes=15, priority=Priority.LOW,    frequency="weekly", preferred_time="19:00"))
luna.add_task(Task(title="Luna breakfast",task_type="feed",     duration_minutes=5,  priority=Priority.HIGH,   is_required=True, preferred_time="07:30"))

# Mark Evening walk complete — demo recurrence
mochi.complete_task("Evening walk")

jordan = Owner(name="Jordan", time_available_per_day=60)
jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(owner=jordan)
WIDTH = 60


def task_rows(tasks, show_pet=False, show_status=False):
    rows = []
    for t in tasks:
        icon  = TASK_TYPE_EMOJI.get(t.task_type, "📋")
        pri   = PRIORITY_EMOJI.get(t.priority.value, "") + " " + t.priority.value.upper()
        time_ = t.preferred_time or "--:--"
        due   = str(t.due_date) if t.due_date else "--"
        row   = [f"{icon} {t.title}", pri, f"{t.duration_minutes} min", time_]
        if show_pet:
            # find which pet owns this task
            for pet in jordan.pets:
                if t in pet.tasks:
                    row.insert(0, pet.name)
                    break
        if show_status:
            row.append("done" if t.completed else "due")
        rows.append(row)
    return rows


# --- Demo 0: recurrence check ---
print("=" * WIDTH)
print("  RECURRENCE CHECK (Evening walk completed)")
print("=" * WIDTH)
headers = ["Task", "Freq", "Due date", "Status"]
rows = [
    [t.title, t.frequency, str(t.due_date) if t.due_date else "--", "✅ done" if t.completed else "⏳ due"]
    for t in mochi.tasks
]
print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))

# --- Demo 1: sort_by_time ---
print()
print("=" * WIDTH)
print("  SORTED BY TIME (all pending tasks)")
print("=" * WIDTH)
all_pending = jordan.get_all_tasks()
headers = ["Pet", "Task", "Priority", "Duration", "Time"]
rows = task_rows(scheduler.sort_by_time(all_pending), show_pet=True)
print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))

# --- Demo 2: filter by pet ---
print()
print("=" * WIDTH)
print("  MOCHI'S TASKS ONLY")
print("=" * WIDTH)
headers = ["Task", "Priority", "Duration", "Time", "Status"]
rows = task_rows(jordan.get_tasks_for_pet("Mochi"), show_status=True)
print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))

# --- Demo 3: completed tasks ---
print()
print("=" * WIDTH)
print("  COMPLETED TASKS")
print("=" * WIDTH)
done = jordan.get_tasks_by_status(completed=True)
if done:
    headers = ["Task", "Priority", "Duration", "Time", "Status"]
    print(tabulate(task_rows(done, show_status=True), headers=headers, tablefmt="rounded_outline"))
else:
    print("  None yet.")

# --- Demo 4: full generated schedule ---
print()
plan = scheduler.generate_plan()
print(plan.get_summary(jordan))
