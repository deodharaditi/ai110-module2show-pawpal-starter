import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- Session state: persist Owner across reruns ---
# st.session_state works like a dictionary. The "if not in" guard ensures we
# only create the Owner once — on every subsequent rerun it already exists.
if "owner" not in st.session_state:
    st.session_state.owner = None   # set after the setup form is submitted

if "setup_done" not in st.session_state:
    st.session_state.setup_done = False


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
        st.rerun()

else:
    owner: Owner = st.session_state.owner
    st.success(f"Owner: {owner.name} | {owner.time_available_per_day} min available today")

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
        st.rerun()

    if owner.pets:
        st.write("**Pets:**", ", ".join(p.get_info() for p in owner.pets))

    # --- Step 3: Add a task to a pet ---
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

        is_required = st.checkbox("Required (must be scheduled)")

        if st.button("Add task"):
            pet = next(p for p in owner.pets if p.name == selected_pet)
            pet.add_task(Task(
                title=task_title,
                task_type="general",
                duration_minutes=int(duration),
                priority=Priority[priority.upper()],
                is_required=is_required,
            ))
            st.rerun()

        all_tasks = owner.get_all_tasks()
        if all_tasks:
            st.write("**Pending tasks:**")
            st.table([t.to_dict() for t in all_tasks])

    # --- Step 4: Generate schedule ---
    st.divider()
    st.subheader("Step 4: Generate today's schedule")
    if st.button("Generate schedule"):
        if not owner.get_all_tasks():
            st.warning("Add at least one task before generating a schedule.")
        else:
            plan = Scheduler(owner).generate_plan()
            st.code(plan.get_summary(owner))
