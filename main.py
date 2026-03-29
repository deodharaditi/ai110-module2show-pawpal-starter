from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# --- Setup ---
mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# Tasks added OUT OF ORDER intentionally to test sort_by_time()
mochi.add_task(Task(
    title="Evening walk",
    task_type="walk",
    duration_minutes=25,
    priority=Priority.MEDIUM,
    preferred_time="18:00",
))
mochi.add_task(Task(
    title="Breakfast",
    task_type="feed",
    duration_minutes=10,
    priority=Priority.HIGH,
    is_required=True,
    preferred_time="07:30",
))
mochi.add_task(Task(
    title="Morning walk",
    task_type="walk",
    duration_minutes=30,
    priority=Priority.HIGH,
    is_required=True,
    preferred_time="08:00",
))
mochi.add_task(Task(
    title="Fetch in the yard",
    task_type="enrichment",
    duration_minutes=20,
    priority=Priority.MEDIUM,
    preferred_time="15:00",
))

luna.add_task(Task(
    title="Medication",
    task_type="meds",
    duration_minutes=5,
    priority=Priority.HIGH,
    is_required=True,
    preferred_time="08:15",
    notes="Half a tablet with food",
))
luna.add_task(Task(
    title="Brush coat",
    task_type="grooming",
    duration_minutes=15,
    priority=Priority.LOW,
    frequency="weekly",
    preferred_time="19:00",
))
# Intentional conflict: same time slot as Mochi's Breakfast
luna.add_task(Task(
    title="Luna breakfast",
    task_type="feed",
    duration_minutes=5,
    priority=Priority.HIGH,
    is_required=True,
    preferred_time="07:30",
))

# Mark Evening walk complete via complete_task() — should auto-queue tomorrow's occurrence
mochi.complete_task("Evening walk")

jordan = Owner(name="Jordan", time_available_per_day=60)
jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(owner=jordan)

# --- Demo 0: recurring task recurrence ---
WIDTH = 60
print("=" * WIDTH)
print("  RECURRENCE CHECK (Evening walk completed)")
print("=" * WIDTH)
for t in mochi.tasks:
    status = "[done]" if t.completed else "[due] "
    due = f"due {t.due_date}" if t.due_date else "no due date"
    print(f"  {status} {t.title.ljust(26)} freq={t.frequency}, {due}")

# --- Demo 1: sort_by_time across all pending tasks ---
print("=" * WIDTH)
print("  SORTED BY TIME (all pending tasks)")
print("=" * WIDTH)
all_pending = jordan.get_all_tasks()
for t in scheduler.sort_by_time(all_pending):
    time_label = t.preferred_time or "no time"
    print(f"  {time_label}  {t.title.ljust(26)} ({t.priority.value})")

# --- Demo 2: filter by pet ---
print()
print("=" * WIDTH)
print("  MOCHI'S TASKS ONLY")
print("=" * WIDTH)
for t in jordan.get_tasks_for_pet("Mochi"):
    print(f"  {t.title.ljust(30)} completed={t.completed}")

# --- Demo 3: filter by completion status ---
print()
print("=" * WIDTH)
print("  COMPLETED TASKS")
print("=" * WIDTH)
done = jordan.get_tasks_by_status(completed=True)
if done:
    for t in done:
        print(f"  [x] {t.title}")
else:
    print("  None yet.")

# --- Demo 4: full generated schedule ---
print()
plan = scheduler.generate_plan()
print(plan.get_summary(jordan))
