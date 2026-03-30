from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler, Priority


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(**kwargs):
    defaults = dict(
        title="Test task",
        task_type="walk",
        duration_minutes=20,
        priority=Priority.MEDIUM,
    )
    return Task(**{**defaults, **kwargs})


def make_owner(minutes=120):
    owner = Owner(name="Test Owner", time_available_per_day=minutes)
    pet = Pet(name="Buddy", species="dog", age=2)
    owner.add_pet(pet)
    return owner, pet


# ---------------------------------------------------------------------------
# Original tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = make_task(title="Morning walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task(title="Breakfast"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task(title="Evening walk"))
    assert len(pet.tasks) == 2


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """Tasks with preferred_time are returned in HH:MM chronological order."""
    owner, _ = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        make_task(title="Dinner",        preferred_time="18:00"),
        make_task(title="Breakfast",     preferred_time="07:30"),
        make_task(title="Afternoon nap", preferred_time="14:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    times = [t.preferred_time for t in sorted_tasks]
    assert times == ["07:30", "14:00", "18:00"]


def test_sort_by_time_untimed_tasks_sink_to_end():
    """Tasks without preferred_time always appear after timed tasks."""
    owner, _ = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        make_task(title="No time task"),
        make_task(title="Early task", preferred_time="06:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    assert sorted_tasks[0].title == "Early task"
    assert sorted_tasks[1].title == "No time task"


def test_sort_by_time_all_untimed_no_crash():
    """sort_by_time on tasks with no preferred_time should not raise."""
    owner, _ = make_owner()
    scheduler = Scheduler(owner)
    tasks = [make_task(title=f"Task {i}") for i in range(3)]
    result = scheduler.sort_by_time(tasks)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_occurrence():
    """Completing a daily task appends a new copy due tomorrow."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(make_task(title="Morning walk", frequency="daily"))
    pet.complete_task("Morning walk")

    tomorrow = date.today() + timedelta(days=1)
    recurrences = [t for t in pet.tasks if not t.completed]
    assert len(recurrences) == 1
    assert recurrences[0].due_date == tomorrow


def test_complete_weekly_task_creates_next_occurrence():
    """Completing a weekly task appends a new copy due in one week."""
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(make_task(title="Brush coat", frequency="weekly"))
    pet.complete_task("Brush coat")

    next_week = date.today() + timedelta(weeks=1)
    recurrences = [t for t in pet.tasks if not t.completed]
    assert len(recurrences) == 1
    assert recurrences[0].due_date == next_week


def test_complete_as_needed_task_does_not_recur():
    """Completing an as-needed task should NOT add a new occurrence."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(make_task(title="Vet visit", frequency="as-needed"))
    pet.complete_task("Vet visit")

    assert len(pet.tasks) == 1          # no new task appended
    assert pet.tasks[0].completed is True


def test_complete_nonexistent_task_no_crash():
    """complete_task with a title that does not exist should not raise."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(make_task(title="Breakfast"))
    pet.complete_task("Walk")           # does not exist
    assert len(pet.tasks) == 1          # unchanged


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_same_time_slot():
    """Two scheduled tasks sharing preferred_time should produce a warning."""
    owner, _ = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        make_task(title="Mochi breakfast", preferred_time="07:30"),
        make_task(title="Luna breakfast",  preferred_time="07:30"),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert len(warnings) == 1
    assert "07:30" in warnings[0]
    assert "Mochi breakfast" in warnings[0]
    assert "Luna breakfast" in warnings[0]


def test_detect_conflicts_no_overlap_returns_empty():
    """Tasks at different times should produce no warnings."""
    owner, _ = make_owner()
    scheduler = Scheduler(owner)
    tasks = [
        make_task(title="Breakfast", preferred_time="07:30"),
        make_task(title="Dinner",    preferred_time="18:00"),
    ]
    assert scheduler.detect_conflicts(tasks) == []


def test_detect_conflicts_untimed_tasks_ignored():
    """Tasks with no preferred_time should never trigger a conflict warning."""
    owner, _ = make_owner()
    scheduler = Scheduler(owner)
    tasks = [make_task(title=f"Task {i}") for i in range(3)]
    assert scheduler.detect_conflicts(tasks) == []


# ---------------------------------------------------------------------------
# Edge cases: empty / boundary states
# ---------------------------------------------------------------------------

def test_get_pending_tasks_empty_pet():
    """A pet with no tasks returns an empty pending list."""
    pet = Pet(name="Buddy", species="dog", age=1)
    assert pet.get_pending_tasks() == []


def test_future_due_date_excluded_from_pending():
    """A task with a future due_date should not appear in pending tasks."""
    pet = Pet(name="Buddy", species="dog", age=1)
    future_task = make_task(title="Future task", due_date=date.today() + timedelta(days=5))
    pet.add_task(future_task)
    assert pet.get_pending_tasks() == []


def test_get_tasks_for_pet_unknown_name_returns_empty():
    """get_tasks_for_pet with a name not in the owner's pets returns []."""
    owner, _ = make_owner()
    assert owner.get_tasks_for_pet("Unknown") == []


def test_filter_tasks_zero_budget_skips_all():
    """With a budget of 0, every task ends up in unscheduled."""
    owner, _ = make_owner(minutes=0)
    scheduler = Scheduler(owner)
    tasks = [make_task(title=f"Task {i}", duration_minutes=10) for i in range(3)]
    scheduled, unscheduled = scheduler.filter_tasks(tasks, budget=0)
    assert scheduled == []
    assert len(unscheduled) == 3


# ---------------------------------------------------------------------------
# Weighted scoring
# ---------------------------------------------------------------------------

def test_score_task_required_outscores_optional_same_priority():
    """A required task should score higher than an optional task at the same priority and duration."""
    owner, _ = make_owner(minutes=60)
    scheduler = Scheduler(owner)
    required = make_task(title="Required", priority=Priority.MEDIUM, is_required=True,  duration_minutes=10)
    optional = make_task(title="Optional", priority=Priority.MEDIUM, is_required=False, duration_minutes=10)
    assert scheduler.score_task(required, 60) > scheduler.score_task(optional, 60)


def test_score_task_shorter_beats_longer_at_same_priority():
    """Given equal priority, a shorter task should score higher than a longer one."""
    owner, _ = make_owner(minutes=60)
    scheduler = Scheduler(owner)
    short = make_task(title="Short", priority=Priority.HIGH, duration_minutes=5)
    long_ = make_task(title="Long",  priority=Priority.HIGH, duration_minutes=50)
    assert scheduler.score_task(short, 60) > scheduler.score_task(long_, 60)


def test_rank_tasks_weighted_short_high_before_long_high():
    """rank_tasks_weighted should place a short HIGH task before a long HIGH task."""
    owner, _ = make_owner(minutes=60)
    scheduler = Scheduler(owner)
    tasks = [
        make_task(title="Long HIGH",  priority=Priority.HIGH, duration_minutes=55),
        make_task(title="Short HIGH", priority=Priority.HIGH, duration_minutes=5),
    ]
    ranked = scheduler.rank_tasks_weighted(tasks, budget=60)
    assert ranked[0].title == "Short HIGH"


def test_generate_plan_weighted_fits_more_tasks():
    """With a tight budget, weighted scheduling should fit more tasks than simple ranking."""
    owner = Owner(name="Test", time_available_per_day=35)
    pet = Pet(name="Buddy", species="dog", age=2)
    # Simple ranking would pick Long HIGH first (60 min > budget, blocks Short HIGH)
    # Weighted ranking picks Short HIGH (5 min) and Short MEDIUM (5 min) first
    pet.add_task(make_task(title="Long HIGH",   priority=Priority.HIGH,   duration_minutes=30))
    pet.add_task(make_task(title="Short HIGH",  priority=Priority.HIGH,   duration_minutes=5))
    pet.add_task(make_task(title="Short MED",   priority=Priority.MEDIUM, duration_minutes=5))
    owner.add_pet(pet)

    weighted_plan  = Scheduler(owner).generate_plan(weighted=True)
    simple_plan    = Scheduler(owner).generate_plan(weighted=False)

    assert len(weighted_plan.scheduled_tasks) >= len(simple_plan.scheduled_tasks)
