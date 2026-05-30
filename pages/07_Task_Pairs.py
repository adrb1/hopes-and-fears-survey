import streamlit as st

from survey_app.shared import (
    bootstrap_page,
    get_task_pairs_for_ui,
    go_to_page,
    render_view_anchor,
)


anchor_id = bootstrap_page(7)
render_view_anchor(anchor_id)


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
        button[kind="primary"],
        button[kind="secondary"] {
            min-height: 170px;
            white-space: pre-wrap;
            text-align: left;
            align-items: flex-start;
            justify-content: flex-start;
            padding: 1.5rem;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US WHAT KIND OF WORKER YOU ARE</h2>
        <p style='font-size: 18px; font-weight: bold;'>
            Imagine it's 10 years from now.<br>
            What tasks do you wish to do yourself and not be done by an Agent?
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
def normalize_pair_session_state():
    """
    Keeps the page safe when Streamlit session_state was created
    before these keys existed, or when old values are still stored.
    """
    if "pair_index" not in st.session_state or not isinstance(st.session_state.pair_index, int):
        st.session_state.pair_index = 0

    if "pair_choices" not in st.session_state or not isinstance(st.session_state.pair_choices, dict):
        st.session_state.pair_choices = {}

    if "active_pair_signature" not in st.session_state:
        st.session_state.active_pair_signature = None

    if "reset_pair_flow" not in st.session_state:
        st.session_state.reset_pair_flow = False


def make_pair_signature(pairs):
    """
    Creates a stable signature for the currently loaded pair list.
    If the DB active pairs change, occupation changes, or order changes,
    this signature changes and the page resets to pair 1.
    """
    return tuple(
        (
            pair.get("pair_id"),
            pair.get("occupation_id"),
            pair.get("dimension", ""),
            pair.get("left", {}).get("task_id"),
            pair.get("right", {}).get("task_id"),
        )
        for pair in pairs
    )


def task_card_text(task):
    title = (task.get("title") or "Untitled task").strip()
    description = (task.get("description") or "").strip()

    if description:
        return f"{title}\n\n{description}"

    return title


def reset_pair_flow(pair_signature):
    st.session_state.active_pair_signature = pair_signature
    st.session_state.pair_index = 0
    st.session_state.pair_choices = {}
    st.session_state.reset_pair_flow = False


# -----------------------------
# Load task pairs
# -----------------------------
normalize_pair_session_state()

task_pairs = get_task_pairs_for_ui()
total_pairs = len(task_pairs
st.caption(
    f"DEBUG: loaded {total_pairs} pairs | "
    f"occupation_id={st.session_state.get('selected_occupation_id')} | "
    f"pair_index={st.session_state.get('pair_index')} | "
    f"pair_ids={[pair.get('pair_id') for pair in task_pairs]} | "
    f"dimensions={[pair.get('dimension') for pair in task_pairs]}"
)                 

# Important: if this happens, the DB pairs did not load and your app is showing MOCK_PAIRS.
# MOCK_PAIRS has exactly 3 items, which is why you were seeing only 3 selections.
if task_pairs and all(pair.get("pair_id", 0) < 0 for pair in task_pairs):
    st.error(
        "Only mock task pairs were loaded. The database pairs did not load, "
        "so the app would show only 3 mock selections."
    )
    st.caption(
        "Check selected_occupation_id, task_pairs.is_active, and get_task_pairs_for_ui()/load_task_pairs()."
    )
    st.stop()

if total_pairs == 0:
    st.error("No active task pairs were loaded for this occupation.")
    st.caption(
        f"selected_occupation_id={st.session_state.get('selected_occupation_id')}"
    )
    st.stop()

current_pair_signature = make_pair_signature(task_pairs)

# Reset if:
# 1. the active DB pair list changed,
# 2. the occupation changed,
# 3. page 6 explicitly requested a reset,
# 4. this is an old session with no signature yet.
if (
    st.session_state.get("reset_pair_flow")
    or st.session_state.get("active_pair_signature") != current_pair_signature
):
    reset_pair_flow(current_pair_signature)

# Never jump automatically to page 8 just because pair_index is stale.
# This was the main reason a user could see only the last 3 of 10.
if st.session_state.pair_index < 0:
    st.session_state.pair_index = 0

if st.session_state.pair_index >= total_pairs:
    st.session_state.pair_index = 0


# -----------------------------
# Current pair
# -----------------------------
current_pair = task_pairs[st.session_state.pair_index]

pair_id = current_pair["pair_id"]
left_task = current_pair["left"]
right_task = current_pair["right"]

existing_choice = st.session_state.pair_choices.get(pair_id, "")


# Optional debug while testing. Change to True if needed.
SHOW_DEBUG = False

if SHOW_DEBUG:
    st.caption(
        f"DEBUG: total_pairs={total_pairs} | "
        f"pair_index={st.session_state.pair_index} | "
        f"selected_occupation_id={st.session_state.get('selected_occupation_id')} | "
        f"pair_ids={[pair.get('pair_id') for pair in task_pairs]}"
    )

    if st.button("Clear pair cache and restart pairs"):
        st.cache_data.clear()
        st.session_state.pair_index = 0
        st.session_state.pair_choices = {}
        st.session_state.active_pair_signature = None
        st.session_state.reset_pair_flow = False
        st.rerun()


st.markdown(
    f"""
    <div style='text-align:center; color:#888; margin-bottom:20px;'>
        {st.session_state.pair_index + 1}/{total_pairs}
    </div>
    """,
    unsafe_allow_html=True,
)


def select_pair_choice(choice):
    st.session_state.pair_choices[pair_id] = choice

    if st.session_state.pair_index + 1 < total_pairs:
        st.session_state.pair_index += 1
        st.rerun()

    go_to_page(8)


# -----------------------------
# Pair cards
# -----------------------------
col_left, col_or, col_right = st.columns([0.45, 0.1, 0.45])

with col_left:
    choose_left = st.button(
        task_card_text(left_task),
        key=f"pair_left_{pair_id}",
        type="primary" if existing_choice == "left" else "secondary",
        use_container_width=True,
    )

with col_or:
    st.markdown(
        """
        <div style='display:flex; align-items:center; justify-content:center; height:170px;'>
            <div style='background:#111; color:white; border-radius:50%; width:48px; height:48px;
                        display:flex; align-items:center; justify-content:center;
                        font-weight:bold; font-size:16px;'>or</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    choose_right = st.button(
        task_card_text(right_task),
        key=f"pair_right_{pair_id}",
        type="primary" if existing_choice == "right" else "secondary",
        use_container_width=True,
    )


# -----------------------------
# Navigation
# -----------------------------
st.markdown("---")

col_prev, _, col_hint = st.columns([0.24, 0.44, 0.32])

with col_prev:
    page7_prev = st.button("← Previous", type="tertiary")

with col_hint:
    st.markdown(
        "<div style='text-align:right; color:#666; font-size:14px; padding-top:10px;'>"
        "Click a task card to continue."
        "</div>",
        unsafe_allow_html=True,
    )


if page7_prev:
    if st.session_state.pair_index > 0:
        st.session_state.pair_index -= 1
        st.rerun()

    go_to_page(6)


if choose_left:
    select_pair_choice("left")

if choose_right:
    select_pair_choice("right")
