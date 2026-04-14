import streamlit as st

from survey_app.shared import FEAR_RATING_OPTIONS, HOPE_RATING_OPTIONS, SHARED_FREQUENCY_OPTIONS, bootstrap_page, finalize_submission_to_db, get_task_pairs_for_ui, go_to_page, option_to_rating, rating_to_option, render_view_anchor


anchor_id = bootstrap_page(8)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>AFTER COMPLETING THE SURVEY</h2>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US ABOUT YOUR FEARS AND HOPES</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown("""
    <div style='background-color: #1a1a1a; color: white; padding: 30px; border-radius: 8px;'>
    <h3 style='text-align: center; margin-bottom: 20px;'>I rate my fears about AI Agents as</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    fears_rating_after = st.select_slider(
        "Fear Level After",
        options=FEAR_RATING_OPTIONS,
        value=rating_to_option(st.session_state.fears_rating_after, FEAR_RATING_OPTIONS),
        label_visibility="collapsed",
        key="fears_after_slider",
    )
    st.markdown("**I fear AI Agents because...**")
    fears_text_after = st.text_area("Fear description after", height=100, placeholder="Write your fears here", label_visibility="collapsed", key="fears_text_after")
    st.markdown(f"**{len(fears_text_after)}/350 (Min. 70 characters)**")
    st.markdown("**To what extent do you believe that your AI Agents fear is shared by most people?**")
    fears_shared_after = st.select_slider("Fear shared after", options=SHARED_FREQUENCY_OPTIONS, value=st.session_state.fears_shared_after if st.session_state.fears_shared_after in SHARED_FREQUENCY_OPTIONS else "Moderately", label_visibility="collapsed", key="fears_shared_after")

with right_col:
    st.markdown("""
    <div style='border: 2px solid #333; padding: 30px; border-radius: 8px; background-color: white;'>
    <h3 style='text-align: center; margin-bottom: 20px; color: black;'>I rate my hopes about AI Agents as</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    hopes_rating_after = st.select_slider(
        "Hope Level After",
        options=HOPE_RATING_OPTIONS,
        value=rating_to_option(st.session_state.hopes_rating_after, HOPE_RATING_OPTIONS),
        label_visibility="collapsed",
        key="hopes_after_slider",
    )
    st.markdown("**I have hope in AI Agents because...**")
    hopes_text_after = st.text_area("Hope description after", height=100, placeholder="Write your hopes here", label_visibility="collapsed", key="hopes_text_after")
    st.markdown(f"**{len(hopes_text_after)}/350 (Min. 70 characters)**")
    st.markdown("**To what extent do you believe that your AI Agents hopes are shared by most people?**")
    hopes_shared_after = st.select_slider("Hope shared after", options=SHARED_FREQUENCY_OPTIONS, value=st.session_state.hopes_shared_after if st.session_state.hopes_shared_after in SHARED_FREQUENCY_OPTIONS else "Moderately", label_visibility="collapsed", key="hopes_shared_after")

st.markdown("---")
col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
with col_prev:
    page8_prev = st.button("← Previous")
with col_next:
    page8_next = st.button("Finish →")

if page8_prev:
    st.session_state.pair_index = max(len(get_task_pairs_for_ui()) - 1, 0)
    go_to_page(7)

if page8_next:
    if len(fears_text_after.strip()) < 70:
        st.error("Fears: Please enter at least 70 characters")
    elif len(fears_text_after) > 350:
        st.error("Fears: Your response exceeds 350 characters")
    elif len(hopes_text_after.strip()) < 70:
        st.error("Hopes: Please enter at least 70 characters")
    elif len(hopes_text_after) > 350:
        st.error("Hopes: Your response exceeds 350 characters")
    elif not fears_shared_after:
        st.error("Fears: Please select how widely your fear is shared")
    elif not hopes_shared_after:
        st.error("Hopes: Please select how widely your hope is shared")
    else:
        st.session_state.fears_rating_after = option_to_rating(fears_rating_after, FEAR_RATING_OPTIONS)
        st.session_state.hopes_rating_after = option_to_rating(hopes_rating_after, HOPE_RATING_OPTIONS)
        try:
            finalize_submission_to_db()
            st.session_state.final_submit_done = True
            st.session_state.final_submit_error = ""
            go_to_page(9)
        except Exception as exc:
            st.session_state.final_submit_done = False
            st.session_state.final_submit_error = str(exc).splitlines()[0]
            st.error(f"Final submission failed: {st.session_state.final_submit_error}")
