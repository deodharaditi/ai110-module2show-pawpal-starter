from dataclasses import dataclass, field
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
        """Return all tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]


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
        """Aggregate pending tasks across all pets -Scheduler's single entry point."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_pending_tasks())
        return tasks


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: dict = field(default_factory=dict)  # task title -> explanation

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
        lines.append("=" * WIDTH)
        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Retrieve, rank, and schedule tasks into a DailyPlan within the owner's time budget."""
        budget = self.owner.get_constraints()["time_available_per_day"]
        all_tasks = self.owner.get_all_tasks()

        ranked = self.rank_tasks(all_tasks)
        scheduled, unscheduled = self.filter_tasks(ranked, budget)

        return DailyPlan(
            scheduled_tasks=scheduled,
            unscheduled_tasks=unscheduled,
            total_duration=sum(t.duration_minutes for t in scheduled),
            reasoning=self._explain(scheduled, unscheduled),
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

    def rank_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks so required items come first, then by priority descending."""
        return sorted(
            tasks,
            key=lambda t: (not t.is_required, -Priority.rank(t.priority))
        )

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
