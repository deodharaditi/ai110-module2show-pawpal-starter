from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int
    health_notes: str = ""

    def get_info(self) -> str:
        pass


@dataclass
class Owner:
    name: str
    time_available_per_day: int  # minutes
    pet: Pet = None

    def get_constraints(self) -> dict:
        pass


@dataclass
class Task:
    title: str
    task_type: str  # e.g. "walk", "feed", "meds", "grooming", "enrichment"
    duration_minutes: int
    priority: str   # "high", "medium", "low"
    is_required: bool = False
    notes: str = ""

    def is_feasible(self, available_minutes: int) -> bool:
        pass

    def to_dict(self) -> dict:
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    unscheduled_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: dict = field(default_factory=dict)  # task title -> explanation

    def get_summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_plan(self) -> DailyPlan:
        pass

    def filter_tasks(self) -> list[Task]:
        pass

    def rank_tasks(self) -> list[Task]:
        pass

    def explain(self) -> dict:
        pass
