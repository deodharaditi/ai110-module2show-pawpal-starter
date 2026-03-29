from pawpal_system import Pet, Task, Priority


def make_task(**kwargs):
    defaults = dict(
        title="Test task",
        task_type="walk",
        duration_minutes=20,
        priority=Priority.MEDIUM,
    )
    return Task(**{**defaults, **kwargs})


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
