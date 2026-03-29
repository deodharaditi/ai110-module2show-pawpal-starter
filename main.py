from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# --- Setup ---
mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# Tasks for Mochi
mochi.add_task(Task(
    title="Morning walk",
    task_type="walk",
    duration_minutes=30,
    priority=Priority.HIGH,
    is_required=True,
))
mochi.add_task(Task(
    title="Breakfast",
    task_type="feed",
    duration_minutes=10,
    priority=Priority.HIGH,
    is_required=True,
))
mochi.add_task(Task(
    title="Fetch in the yard",
    task_type="enrichment",
    duration_minutes=20,
    priority=Priority.MEDIUM,
))

# Tasks for Luna
luna.add_task(Task(
    title="Medication",
    task_type="meds",
    duration_minutes=5,
    priority=Priority.HIGH,
    is_required=True,
    notes="Half a tablet with food",
))
luna.add_task(Task(
    title="Brush coat",
    task_type="grooming",
    duration_minutes=15,
    priority=Priority.LOW,
    frequency="weekly",
))

# Owner with 60 minutes available today
jordan = Owner(name="Jordan", time_available_per_day=60)
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner=jordan)
plan = scheduler.generate_plan()

# --- Output ---
print(plan.get_summary(jordan))
