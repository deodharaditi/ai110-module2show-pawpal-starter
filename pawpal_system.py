from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from enum import Enum


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @staticmethod
    def rank(priority: "Priority") -> int:
        return {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}[priority]


@dataclass
class Task:
    title: str
    task_type: str          # "walk", "feed", "meds", "grooming", "enrichment"
    duration_minutes: int
    priority: Priority
    frequency: str = "daily"  # "daily", "weekly", "as-needed"
    is_required: bool = False
    notes: str = ""
    completed: bool = False
    preferred_time: str | None = None  # "HH:MM" format, e.g. "07:30"
    due_date: date | None = None       # None = available any day

    def is_feasible(self, available_minutes: int) -> bool:
        """Return True if this task fits within the given time budget."""
        return self.duration_minutes <= available_minutes

    def mark_complete(self):
        """Mark this task as done so it is excluded from future plans."""
        self.completed = True

    def to_dict(self) -> dict:
        """Serialize this task to a plain dict for display or storage."""
        return {
            "title": self.title,
            "task_type": self.task_type,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.value,
            "frequency": self.frequency,
            "is_required": self.is_required,
            "notes": self.notes,
            "completed": self.completed,
            "preferred_time": self.preferred_time or "--",
            "due_date": str(self.due_date) if self.due_date else "--",
        }


@dataclass
class Pet:
    name: str
    species: str
    age: int
    health_notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def get_info(self) -> str:
        """Return a short readable description of this pet."""
        return f"{self.name} ({self.species}, age {self.age})"

    def add_task(self, task: Task):
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str):
        """Remove the task with the given title from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are incomplete and due today or earlier (no due_date = always due)."""
        today = date.today()
        return [
            t for t in self.tasks
            if not t.completed and (t.due_date is None or t.due_date <= today)
        ]

    def complete_task(self, title: str):
        """Mark a task complete and, if it recurs, append the next occurrence.

        Uses timedelta so date arithmetic handles month and year boundaries:
          daily  -> due_date = today + timedelta(days=1)
          weekly -> due_date = today + timedelta(weeks=1)
          as-needed -> no recurrence; task is simply marked done.
        """
        task = next((t for t in self.tasks if t.title == title and not t.completed), None)
        if not task:
            return
        task.mark_complete()
        recurrence = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
        delta = recurrence.get(task.frequency)
        if delta:
            self.tasks.append(replace(task, completed=False, due_date=date.today() + delta))


@dataclass
class Owner:
    name: str
    time_available_per_day: int  # minutes
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's household."""
        self.pets.append(pet)

    def get_constraints(self) -> dict:
        """Return the owner's scheduling constraints (time budget)."""
        return {"time_available_per_day": self.time_available_per_day}

    def get_all_tasks(self) -> list[Task]:
        """Aggregate pending tasks across all pets - Scheduler's single entry point."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return pending tasks belonging to the named pet, or [] if pet not found."""
        pet = next((p for p in self.pets if p.name.lower() == pet_name.lower()), None)
        return pet.get_pending_tasks() if pet else []

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Return all tasks across all pets that match the given completion status."""
        return [t for p in self.pets for t in p.tasks if t.completed == completed]


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: dict = field(default_factory=dict)   # task title -> explanation
    conflicts: list[str] = field(default_factory=list)  # warning messages

    def get_summary(self, owner: "Owner") -> str:
        """Render a formatted terminal view of the plan, grouped by pet."""
        WIDTH = 60
        scheduled_set = {t.title for t in self.scheduled_tasks}
        budget = owner.time_available_per_day
        bar_filled = round((self.total_duration / budget) * 20) if budget else 0
        bar = "#" * bar_filled + "-" * (20 - bar_filled)

        lines = []
        lines.append("=" * WIDTH)
        lines.append(f"  PawPal+ - Today's Schedule  |  {owner.name}  |  {budget} min")
        lines.append("=" * WIDTH)

        for pet in owner.pets:
            pending = pet.get_pending_tasks()
            if not pending:
                continue
            header = f"  {pet.name.upper()} ({pet.species}, age {pet.age})"
            lines.append("")
            lines.append(header)
            lines.append("  " + "-" * (len(header) - 2))
            for task in pending:
                scheduled = task.title in scheduled_set
                checkbox = "[x]" if scheduled else "[ ]"
                pri = task.priority.value.upper()
                req = "  *required" if task.is_required else ""
                skip = "  -- skipped, no time" if not scheduled else ""
                title_col = task.title.ljust(26)
                dur_col = f"{task.duration_minutes} min".rjust(6)
                lines.append(f"  {checkbox} {title_col} {dur_col}   {pri}{req}{skip}")

        skipped_min = sum(t.duration_minutes for t in self.unscheduled_tasks)
        lines.append("")
        lines.append("-" * WIDTH)
        lines.append(f"  Scheduled  {len(self.scheduled_tasks)} tasks    "
                     f"{self.total_duration} / {budget} min  [{bar}]")
        if self.unscheduled_tasks:
            lines.append(f"  Skipped    {len(self.unscheduled_tasks)} task{'s' if len(self.unscheduled_tasks) > 1 else ''}     "
                         f"{skipped_min} min unscheduled")
        if self.conflicts:
            lines.append("")
            lines.append("  WARNINGS")
            for warning in self.conflicts:
                lines.append(f"  [!] {warning}")
        lines.append("=" * WIDTH)
        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self, weighted: bool = True) -> DailyPlan:
        """Retrieve, rank, and schedule tasks into a DailyPlan within the owner's time budget.

        When weighted=True (default), uses score_task() for ranking so that time
        efficiency is factored in alongside priority and required status.
        When weighted=False, falls back to the simpler rank_tasks() sort.
        """
        budget = self.owner.get_constraints()["time_available_per_day"]
        all_tasks = self.owner.get_all_tasks()

        ranked = self.rank_tasks_weighted(all_tasks, budget) if weighted else self.rank_tasks(all_tasks)
        scheduled, unscheduled = self.filter_tasks(ranked, budget)

        return DailyPlan(
            scheduled_tasks=scheduled,
            unscheduled_tasks=unscheduled,
            total_duration=sum(t.duration_minutes for t in scheduled),
            reasoning=self._explain(scheduled, unscheduled),
            conflicts=self.detect_conflicts(scheduled),
        )

    def filter_tasks(self, tasks: list[Task], budget: int) -> tuple[list[Task], list[Task]]:
        """Greedily assign tasks in priority order until the time budget is exhausted."""
        scheduled, unscheduled = [], []
        remaining = budget
        for task in tasks:
            if task.is_feasible(remaining):
                scheduled.append(task)
                remaining -= task.duration_minutes
            else:
                unscheduled.append(task)
        return scheduled, unscheduled

    def score_task(self, task: Task, budget: int) -> float:
        """Compute a numeric score for a task used by rank_tasks_weighted().

        Score formula:
          base        = priority rank (HIGH=3, MEDIUM=2, LOW=1)
          required    = +10 bonus so required tasks always outrank optional ones
          efficiency  = base / (duration_minutes / budget)
                        rewards tasks that deliver high priority per minute of budget used

        A 5-min HIGH task and a 60-min HIGH task both have base=3, but the
        5-min task has a much higher efficiency score when budget is tight,
        so it is scheduled first — leaving more room for other tasks.
        """
        base = Priority.rank(task.priority)
        required_bonus = 10 if task.is_required else 0
        duration_fraction = task.duration_minutes / budget if budget > 0 else 1
        efficiency = base / duration_fraction
        return required_bonus + efficiency

    def rank_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks so required items come first, then by priority descending."""
        return sorted(
            tasks,
            key=lambda t: (not t.is_required, -Priority.rank(t.priority))
        )

    def rank_tasks_weighted(self, tasks: list[Task], budget: int) -> list[Task]:
        """Sort tasks by weighted score descending using score_task().

        Produces a different ordering than rank_tasks() when high-priority tasks
        have very different durations — shorter high-priority tasks float above
        longer ones of equal priority, maximising the number of tasks that fit.
        """
        return sorted(tasks, key=lambda t: self.score_task(t, budget), reverse=True)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by preferred_time in HH:MM order; tasks with no time sink to the end.

        "HH:MM" strings sort correctly as plain strings because lexicographic
        order matches chronological order when the format is zero-padded.
        e.g. "07:00" < "09:30" < "14:00" < "99:99" (sentinel for no preference).
        """
        return sorted(
            tasks,
            key=lambda t: t.preferred_time if t.preferred_time else "99:99"
        )

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning strings for any time slot shared by more than one scheduled task.

        Lightweight strategy: group tasks by preferred_time using a dict, then
        flag any slot with multiple entries. Tasks with no preferred_time are
        skipped — they have no fixed slot to conflict on.
        """
        warnings = []
        by_time: dict[str, list[str]] = defaultdict(list)
        for task in tasks:
            if task.preferred_time:
                by_time[task.preferred_time].append(task.title)
        for time_slot, titles in by_time.items():
            if len(titles) > 1:
                warnings.append(
                    f"Time conflict at {time_slot}: {' and '.join(titles)}"
                )
        return warnings

    def _explain(self, scheduled: list[Task], unscheduled: list[Task]) -> dict:
        """Build a per-task reasoning dict describing why each task was included or skipped."""
        reasoning = {}
        for task in scheduled:
            tag = "Required - " if task.is_required else ""
            reasoning[task.title] = f"{tag}priority {task.priority.value}, fits in time budget."
        for task in unscheduled:
            tag = "Required but " if task.is_required else ""
            reasoning[task.title] = f"{tag}exceeds remaining time - priority {task.priority.value}, skipped."
        return reasoning
