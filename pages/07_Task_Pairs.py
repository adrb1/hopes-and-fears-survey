import streamlit as st

from survey_app.shared import bootstrap_page, get_task_pairs_for_ui, go_to_page, render_view_anchor


anchor_id = bootstrap_page(7)
render_view_anchor(anchor_id)

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

with st.form(f"page7_pair_form_{pair_id}"):
    col_left, col_or, col_right = st.columns([0.45, 0.1, 0.45])
    with col_left:
        border_left = "3px solid #E63946" if existing_choice == "left" else "2px solid #333"
        st.markdown(f"""
        <div style='border:{border_left}; padding:30px; border-radius:8px; min-height:160px; background:{'#fff5f5' if existing_choice == 'left' else 'white'};'>
            <strong>{left_task['title']}</strong>
            <p style='color:#555; font-size:14px; margin-top:10px;'>{left_task['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_or:
        st.markdown("""
        <div style='display:flex; align-items:center; justify-content:center; height:160px;'>
            <div style='background:#111; color:white; border-radius:50%; width:48px; height:48px;
                        display:flex; align-items:center; justify-content:center;
                        font-weight:bold; font-size:16px;'>or</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        border_right = "3px solid #E63946" if existing_choice == "right" else "2px solid #333"
        st.markdown(f"""
        <div style='border:{border_right}; padding:30px; border-radius:8px; min-height:160px; background:{'#fff5f5' if existing_choice == 'right' else 'white'};'>
            <strong>{right_task['title']}</strong>
            <p style='color:#555; font-size:14px; margin-top:10px;'>{right_task['description']}</p>
        </div>
        """, unsafe_allow_html=True)

    selected_choice = st.radio("Which task would you prefer to keep doing yourself?", options=["left", "right"], index=["left", "right"].index(existing_choice) if existing_choice in {"left", "right"} else None, format_func=lambda value: left_task["title"] if value == "left" else right_task["title"], horizontal=True, key=f"pair_choice_{pair_id}")

    st.markdown("---")
    col_prev, _, col_next = st.columns([0.24, 0.52, 0.24])
    with col_prev:
        page7_prev = st.form_submit_button("← Previous")
    with col_next:
        page7_next = st.form_submit_button("Finish →" if st.session_state.pair_index == total_pairs - 1 else "Next →")

if page7_prev:
    if st.session_state.pair_index > 0:
        st.session_state.pair_index -= 1
        st.rerun()
    st.session_state.page6_question_index = max(st.session_state.get("page6_total_questions", 14) - 1, 0)
    go_to_page(6)

if page7_next:
    if selected_choice not in {"left", "right"}:
        st.error("Please choose one task.")
    else:
        st.session_state.pair_choices[pair_id] = selected_choice
        st.session_state.pair_index += 1
        st.rerun()
