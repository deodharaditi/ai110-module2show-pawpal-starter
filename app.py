import os

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

DATA_FILE = "data.json"

# ---------------------------------------------------------------------------
# Display constants
# ---------------------------------------------------------------------------

PRIORITY_STYLE = {
    "high":   {"emoji": "🔴", "bg": "#3d1a1a", "border": "#8b0000", "label": "HIGH"},
    "medium": {"emoji": "🟡", "bg": "#3d3519", "border": "#8b7000", "label": "MED"},
    "low":    {"emoji": "🟢", "bg": "#1a3d22", "border": "#006400", "label": "LOW"},
}

TASK_TYPE_EMOJI = {
    "walk":       "🦮",
    "feed":       "🍖",
    "meds":       "💊",
    "grooming":   "✂️",
    "enrichment": "🎾",
    "general":    "📋",
}

SPECIES_EMOJI = {
    "dog":   "🐶",
    "cat":   "🐱",
    "other": "🐾",
}


def _step_header(number: int, label: str) -> None:
    st.markdown(
        f"<p style='margin:18px 0 4px;font-size:0.78em;font-weight:700;"
        f"letter-spacing:0.08em;opacity:0.55;text-transform:uppercase;'>"
        f"STEP {number}</p>"
        f"<h3 style='margin:0 0 12px;'>{label}</h3>",
        unsafe_allow_html=True,
    )


def _task_card(task: Task, scheduled: bool | None = None, pet_name: str = "") -> None:
    """Render a colour-coded task card with type emoji, priority badge, and status icon."""
    pval   = task.priority.value
    style  = PRIORITY_STYLE.get(pval, PRIORITY_STYLE["low"])
    ticon  = TASK_TYPE_EMOJI.get(task.task_type, "📋")
    time_str = task.preferred_time or "--:--"

    badges = []
    if task.is_required:
        badges.append("⭐ required")
    if pet_name:
        badges.append(pet_name)
    badge_html = " &nbsp;".join(
        f"<span style='background:rgba(255,255,255,0.08);border-radius:4px;"
        f"padding:1px 6px;font-size:0.78em;'>{b}</span>"
        for b in badges
    )

    if scheduled is True:
        status = "<span style='float:right;font-size:1.1em;'>✅</span>"
    elif scheduled is False:
        status = "<span style='float:right;font-size:1.1em;opacity:0.5;'>❌ skipped</span>"
    else:
        status = ""

    st.markdown(
        f"""<div style="background:{style['bg']};border-left:3px solid {style['border']};
        border-radius:6px;padding:9px 14px;margin:4px 0;line-height:1.6;">
        {status}
        {ticon} <strong>{task.title}</strong> &nbsp; {badge_html}<br>
        <span style="opacity:0.65;font-size:0.85em;">
            {style['emoji']} {style['label']} &nbsp;·&nbsp;
            🕐 {time_str} &nbsp;·&nbsp;
            ⏱ {task.duration_minutes} min
            {"&nbsp;·&nbsp; 🔁 " + task.frequency if task.frequency != "daily" else ""}
        </span>
        </div>""",
        unsafe_allow_html=True,
    )


def _pet_header(pet: Pet) -> None:
    icon = SPECIES_EMOJI.get(pet.species, "🐾")
    st.markdown(
        f"<div style='margin:14px 0 6px;padding:6px 12px;background:rgba(255,255,255,0.05);"
        f"border-radius:6px;font-weight:600;'>"
        f"{icon} {pet.name} &nbsp;"
        f"<span style='opacity:0.5;font-size:0.85em;font-weight:400;'>"
        f"{pet.species}, age {pet.age}</span></div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.markdown(
    "<h1 style='margin-bottom:0;'>🐾 PawPal+</h1>"
    "<p style='opacity:0.5;margin-top:2px;'>Daily pet care scheduler</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state — load saved data on first run
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    saved = Owner.load_from_json(DATA_FILE)
    st.session_state.owner = saved
    st.session_state.setup_done = saved is not None

if "setup_done" not in st.session_state:
    st.session_state.setup_done = False


def _save():
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)
    st.rerun()


# ---------------------------------------------------------------------------
# Step 1 — Owner setup
# ---------------------------------------------------------------------------

if not st.session_state.setup_done:
    _step_header(1, "Tell us about you")
    owner_name    = st.text_input("Your name", value="Jordan")
    time_available = st.number_input(
        "Minutes available for pet care today", min_value=10, max_value=480, value=60
    )
    if st.button("Save owner info", type="primary"):
        st.session_state.owner = Owner(
            name=owner_name,
            time_available_per_day=int(time_available),
        )
        st.session_state.setup_done = True
        _save()

else:
    owner: Owner = st.session_state.owner

    # Owner banner
    col_hdr, col_reset = st.columns([5, 1])
    with col_hdr:
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.05);border-radius:6px;"
            f"padding:8px 14px;margin-bottom:8px;'>"
            f"👤 <strong>{owner.name}</strong> &nbsp;·&nbsp; "
            f"⏱ {owner.time_available_per_day} min available today</div>",
            unsafe_allow_html=True,
        )
    with col_reset:
        if st.button("Reset", help="Clear saved data and start over"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.session_state.owner = None
            st.session_state.setup_done = False
            st.rerun()

    st.divider()

    # -----------------------------------------------------------------------
    # Step 2 — Add a pet
    # -----------------------------------------------------------------------

    _step_header(2, "Add a pet")
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"],
                               format_func=lambda s: f"{SPECIES_EMOJI.get(s, '🐾')} {s}")
    with col3:
        age = st.number_input("Age", min_value=0, max_value=30, value=3)

    if st.button("Add pet", type="primary"):
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
        _save()

    if owner.pets:
        cols = st.columns(len(owner.pets))
        for col, pet in zip(cols, owner.pets):
            icon = SPECIES_EMOJI.get(pet.species, "🐾")
            col.metric(f"{icon} {pet.name}", f"{pet.species}, {pet.age}y")

    st.divider()

    # -----------------------------------------------------------------------
    # Step 3 — Add a task
    # -----------------------------------------------------------------------

    _step_header(3, "Add a task")
    if not owner.pets:
        st.info("Add a pet first before adding tasks.")
    else:
        pet_names = [p.name for p in owner.pets]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_pet = st.selectbox("Pet", pet_names)
        with col2:
            task_title = st.text_input("Task name", value="Morning walk")
        with col3:
            task_type = st.selectbox(
                "Type",
                list(TASK_TYPE_EMOJI.keys()),
                format_func=lambda t: f"{TASK_TYPE_EMOJI[t]} {t}",
            )
        with col4:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            priority = st.selectbox(
                "Priority",
                ["high", "medium", "low"],
                format_func=lambda p: f"{PRIORITY_STYLE[p]['emoji']} {p}",
            )
        with col_b:
            preferred_time = st.text_input("Preferred time (HH:MM)", value="")
        with col_c:
            is_required = st.checkbox("Required")

        if st.button("Add task", type="primary"):
            pet = next(p for p in owner.pets if p.name == selected_pet)
            pet.add_task(Task(
                title=task_title,
                task_type=task_type,
                duration_minutes=int(duration),
                priority=Priority[priority.upper()],
                is_required=is_required,
                preferred_time=preferred_time.strip() or None,
            ))
            _save()

        # --- Pending task list ---
        all_tasks = owner.get_all_tasks()
        if all_tasks:
            st.divider()

            # Quick stats
            hi = sum(1 for t in all_tasks if t.priority == Priority.HIGH)
            md = sum(1 for t in all_tasks if t.priority == Priority.MEDIUM)
            lo = sum(1 for t in all_tasks if t.priority == Priority.LOW)
            total_min = sum(t.duration_minutes for t in all_tasks)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tasks", len(all_tasks))
            c2.metric("🔴 High", hi)
            c3.metric("🟡 Medium", md)
            c4.metric("Total time", f"{total_min} min")

            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                filter_pet = st.selectbox(
                    "Filter by pet", ["All pets"] + pet_names, key="filter_pet"
                )
            with filter_col2:
                sort_mode = st.selectbox(
                    "Sort by",
                    ["Priority → Time", "Preferred time", "Priority only"],
                    key="sort_mode",
                )

            display_tasks = (
                all_tasks if filter_pet == "All pets"
                else owner.get_tasks_for_pet(filter_pet)
            )

            scheduler = Scheduler(owner)
            if sort_mode == "Priority → Time":
                display_tasks = scheduler.sort_by_priority_then_time(display_tasks)
            elif sort_mode == "Preferred time":
                display_tasks = scheduler.sort_by_time(display_tasks)
            else:
                display_tasks = scheduler.rank_tasks(display_tasks)

            conflicts = scheduler.detect_conflicts(display_tasks)
            if conflicts:
                for warning in conflicts:
                    st.warning(f"⚠️ {warning} — adjust the preferred time for one of these tasks.")

            # Show which pet owns each task when viewing all pets
            pet_lookup = {t.title: p.name for p in owner.pets for t in p.tasks}
            for task in display_tasks:
                pname = pet_lookup.get(task.title, "") if filter_pet == "All pets" else ""
                _task_card(task, pet_name=pname)

    st.divider()

    # -----------------------------------------------------------------------
    # Step 4 — Generate schedule
    # -----------------------------------------------------------------------

    _step_header(4, "Generate today's schedule")
    if st.button("Generate schedule", type="primary"):
        if not owner.get_all_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            scheduler = Scheduler(owner)
            plan      = scheduler.generate_plan()
            budget    = owner.time_available_per_day
            used      = plan.total_duration
            pct       = min(used / budget, 1.0) if budget else 0

            # Summary metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Scheduled", len(plan.scheduled_tasks))
            m2.metric("Skipped",   len(plan.unscheduled_tasks))
            m3.metric("Time used", f"{used} min")
            m4.metric("Remaining", f"{budget - used} min")

            # Progress bar — colour via caption
            bar_label = f"{round(pct * 100)}% of daily budget used"
            st.progress(pct, text=bar_label)

            # Conflict warnings
            if plan.conflicts:
                st.markdown(
                    "<p style='font-weight:700;margin-top:16px;'>⚠️ Scheduling conflicts</p>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    "These tasks share the same preferred time. Both are scheduled — "
                    "update one to avoid overlap."
                )
                for warning in plan.conflicts:
                    st.warning(warning)

            # Per-pet task breakdown
            scheduled_titles = {t.title for t in plan.scheduled_tasks}
            for pet in owner.pets:
                pending = pet.get_pending_tasks()
                if not pending:
                    continue
                _pet_header(pet)
                for task in scheduler.sort_by_priority_then_time(pending):
                    _task_card(task, scheduled=task.title in scheduled_titles)

            # Footer message
            if plan.unscheduled_tasks:
                skipped_min = sum(t.duration_minutes for t in plan.unscheduled_tasks)
                st.info(
                    f"**{len(plan.unscheduled_tasks)} task(s) skipped** ({skipped_min} min) — "
                    f"increase your daily budget to fit them in."
                )
            else:
                st.success("✅ All tasks fit within today's time budget.")
