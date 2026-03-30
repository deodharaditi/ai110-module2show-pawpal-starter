import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# Priority display config — emoji badge + CSS background colour per level
PRIORITY_STYLE = {
    "high":   {"emoji": "🔴", "bg": "#3d1a1a", "label": "HIGH"},
    "medium": {"emoji": "🟡", "bg": "#3d3519", "label": "MED"},
    "low":    {"emoji": "🟢", "bg": "#1a3d22", "label": "LOW"},
}


def _task_card(task: Task, scheduled: bool | None = None) -> None:
    """Render a single task as a colour-coded card using st.markdown."""
    pval = task.priority.value
    style = PRIORITY_STYLE.get(pval, PRIORITY_STYLE["low"])
    time_str = task.preferred_time or "--:--"
    req_tag = " ⭐ required" if task.is_required else ""

    if scheduled is True:
        status_icon = "✅"
    elif scheduled is False:
        status_icon = "❌"
    else:
        status_icon = ""

    st.markdown(
        f"""<div style="background:{style['bg']};border-radius:6px;padding:8px 12px;margin:4px 0;">
        {style['emoji']} <strong>{task.title}</strong>{req_tag} &nbsp;
        <code>{time_str}</code> &nbsp;·&nbsp; {task.duration_minutes} min &nbsp;·&nbsp;
        <span style="font-size:0.85em;opacity:0.8;">{style['label']}</span>
        {"&nbsp;" + status_icon if status_icon else ""}
        </div>""",
        unsafe_allow_html=True,
    )

DATA_FILE = "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state: load saved data on first run ---
if "owner" not in st.session_state:
    saved = Owner.load_from_json(DATA_FILE)
    st.session_state.owner = saved
    st.session_state.setup_done = saved is not None

if "setup_done" not in st.session_state:
    st.session_state.setup_done = False


def _save():
    """Persist current owner state to disk, then rerun the UI."""
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)
    st.rerun()


# --- Step 1: Owner setup ---
if not st.session_state.setup_done:
    st.subheader("Step 1: Tell us about you")
    owner_name = st.text_input("Your name", value="Jordan")
    time_available = st.number_input(
        "Minutes available for pet care today", min_value=10, max_value=480, value=60
    )
    if st.button("Save owner info"):
        st.session_state.owner = Owner(
            name=owner_name,
            time_available_per_day=int(time_available),
        )
        st.session_state.setup_done = True
        _save()

else:
    owner: Owner = st.session_state.owner
    col_hdr, col_reset = st.columns([4, 1])
    with col_hdr:
        st.success(f"Owner: **{owner.name}** | {owner.time_available_per_day} min available today")
    with col_reset:
        if st.button("Reset", help="Clear saved data and start over"):
            import os
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.session_state.owner = None
            st.session_state.setup_done = False
            st.rerun()

    # --- Step 2: Add a pet ---
    st.subheader("Step 2: Add a pet")
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=30, value=3)

    if st.button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
        _save()

    if owner.pets:
        st.write("**Pets in household:**", ", ".join(p.get_info() for p in owner.pets))

    # --- Step 3: Add a task ---
    st.subheader("Step 3: Add a task")
    if not owner.pets:
        st.info("Add a pet first before adding tasks.")
    else:
        pet_names = [p.name for p in owner.pets]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_pet = st.selectbox("Pet", pet_names)
        with col2:
            task_title = st.text_input("Task", value="Morning walk")
        with col3:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col4:
            priority = st.selectbox("Priority", ["high", "medium", "low"])

        col_a, col_b = st.columns(2)
        with col_a:
            is_required = st.checkbox("Required (must be scheduled)")
        with col_b:
            preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")

        if st.button("Add task"):
            pet = next(p for p in owner.pets if p.name == selected_pet)
            pet.add_task(Task(
                title=task_title,
                task_type="general",
                duration_minutes=int(duration),
                priority=Priority[priority.upper()],
                is_required=is_required,
                preferred_time=preferred_time.strip() or None,
            ))
            _save()

        # --- Pending task view with sorting and filtering ---
        all_tasks = owner.get_all_tasks()
        if all_tasks:
            st.divider()
            st.subheader("Pending tasks")

            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                filter_pet = st.selectbox(
                    "Filter by pet",
                    ["All pets"] + pet_names,
                    key="filter_pet",
                )
            with filter_col2:
                sort_mode = st.selectbox(
                    "Sort by",
                    ["Priority → Time", "Preferred time", "Priority only"],
                    key="sort_mode",
                )

            if filter_pet == "All pets":
                display_tasks = all_tasks
            else:
                display_tasks = owner.get_tasks_for_pet(filter_pet)

            scheduler = Scheduler(owner)
            if sort_mode == "Priority → Time":
                display_tasks = scheduler.sort_by_priority_then_time(display_tasks)
            elif sort_mode == "Preferred time":
                display_tasks = scheduler.sort_by_time(display_tasks)
            else:
                display_tasks = scheduler.rank_tasks(display_tasks)

            conflicts = scheduler.detect_conflicts(display_tasks)
            if conflicts:
                st.markdown("**Scheduling conflicts detected:**")
                for warning in conflicts:
                    st.warning(f"⚠️ {warning} — consider adjusting the preferred time for one of these tasks.")

            for task in display_tasks:
                _task_card(task)

    # --- Step 4: Generate schedule ---
    st.divider()
    st.subheader("Step 4: Generate today's schedule")
    if st.button("Generate schedule"):
        if not owner.get_all_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(owner)
            plan = scheduler.generate_plan()

            budget = owner.time_available_per_day
            used = plan.total_duration
            pct = min(used / budget, 1.0) if budget else 0
            st.markdown(f"**Time used:** {used} / {budget} min")
            st.progress(pct)

            if plan.conflicts:
                st.markdown("### ⚠️ Scheduling conflicts")
                st.caption(
                    "The tasks below share the same preferred time. "
                    "Both are still scheduled — update their times to avoid overlap."
                )
                for warning in plan.conflicts:
                    st.warning(warning)

            scheduled_titles = {t.title for t in plan.scheduled_tasks}
            for pet in owner.pets:
                pending = pet.get_pending_tasks()
                if not pending:
                    continue
                st.markdown(f"**{pet.name}** ({pet.species}, age {pet.age})")
                for task in scheduler.sort_by_priority_then_time(pending):
                    _task_card(task, scheduled=task.title in scheduled_titles)

            if plan.unscheduled_tasks:
                skipped_min = sum(t.duration_minutes for t in plan.unscheduled_tasks)
                st.info(
                    f"{len(plan.unscheduled_tasks)} task(s) skipped "
                    f"({skipped_min} min) — increase your daily time budget to fit them in."
                )
            else:
                st.success("All tasks fit within today's time budget.")
