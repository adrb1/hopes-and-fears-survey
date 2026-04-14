import streamlit as st

from survey_app.shared import bootstrap_page, get_task_pairs_for_ui, go_to_page, render_view_anchor


anchor_id = bootstrap_page(7)
render_view_anchor(anchor_id)

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

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US WHAT KIND OF WORKER YOU ARE</h2>
        <p style='font-size: 18px; font-weight: bold;'>Imagine it's 10 years from now.<br>What tasks do you wish to do yourself and not be done by an Agent?</p>
    </div>
    """,
    unsafe_allow_html=True,
)

task_pairs = get_task_pairs_for_ui()
total_pairs = len(task_pairs)
if st.session_state.pair_index >= total_pairs:
    go_to_page(8)

current_pair = task_pairs[st.session_state.pair_index]
pair_id = current_pair["pair_id"]
left_task = current_pair["left"]
right_task = current_pair["right"]
existing_choice = st.session_state.pair_choices.get(pair_id, "")

st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:20px;'>{st.session_state.pair_index + 1}/{total_pairs}</div>", unsafe_allow_html=True)

def select_pair_choice(choice):
    st.session_state.pair_choices[pair_id] = choice
    if st.session_state.pair_index < total_pairs - 1:
        st.session_state.pair_index += 1
        st.rerun()
    go_to_page(8)


col_left, col_or, col_right = st.columns([0.45, 0.1, 0.45])
with col_left:
    choose_left = st.button(
        f"{left_task['title']}\n\n{left_task['description']}",
        key=f"pair_left_{pair_id}",
        type="primary" if existing_choice == "left" else "secondary",
        use_container_width=True,
    )

with col_or:
    st.markdown("""
    <div style='display:flex; align-items:center; justify-content:center; height:170px;'>
        <div style='background:#111; color:white; border-radius:50%; width:48px; height:48px;
                    display:flex; align-items:center; justify-content:center;
                    font-weight:bold; font-size:16px;'>or</div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    choose_right = st.button(
        f"{right_task['title']}\n\n{right_task['description']}",
        key=f"pair_right_{pair_id}",
        type="primary" if existing_choice == "right" else "secondary",
        use_container_width=True,
    )

st.markdown("---")
col_prev, _, col_hint = st.columns([0.24, 0.44, 0.32])
with col_prev:
    page7_prev = st.button("← Previous", type="tertiary")
with col_hint:
    st.markdown(
        "<div style='text-align:right; color:#666; font-size:14px; padding-top:10px;'>Click a task card to continue.</div>",
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
