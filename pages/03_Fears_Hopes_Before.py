import streamlit as st

from survey_app.shared import FEAR_RATING_OPTIONS, HOPE_RATING_OPTIONS, SHARED_FREQUENCY_OPTIONS, bootstrap_page, go_to_page, option_to_rating, rating_to_option, render_view_anchor


anchor_id = bootstrap_page(3)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US ABOUT</h2>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>YOUR FEARS AND HOPES</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("page3_form"):
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown(
            """
            <div style='background-color: #1a1a1a; color: white; padding: 30px; border-radius: 8px;'>
            <h3 style='text-align: center; margin-bottom: 20px;'>I rate my fears about AI Agents as</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fears_rating = st.select_slider(
            "Fear Level",
            options=FEAR_RATING_OPTIONS,
            value=rating_to_option(st.session_state.fears_rating, FEAR_RATING_OPTIONS),
            label_visibility="collapsed",
            key="fears_slider",
        )
        st.markdown("**I fear AI Agents because...**")
        fears_text = st.text_area("Fear description", value=st.session_state.fears_text, height=100, placeholder="Write your fears here", label_visibility="collapsed", key="fears_input")
        st.markdown(f"**{len(fears_text)}/350 (Min. 70 characters)**")
        st.markdown("**To what extent do you believe that your AI Agents fear is shared by most people?**")
        fears_shared = st.select_slider(
            "Fear shared",
            options=SHARED_FREQUENCY_OPTIONS,
            value=st.session_state.fears_shared if st.session_state.fears_shared in SHARED_FREQUENCY_OPTIONS else "Moderately",
            label_visibility="collapsed",
            key="fears_shared_input",
        )

    with right_col:
        st.markdown(
            """
            <div style='border: 2px solid #333; padding: 30px; border-radius: 8px; background-color: white;'>
            <h3 style='text-align: center; margin-bottom: 20px; color: black;'>I rate my hopes about AI Agents as</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        hopes_rating = st.select_slider(
            "Hope Level",
            options=HOPE_RATING_OPTIONS,
            value=rating_to_option(st.session_state.hopes_rating, HOPE_RATING_OPTIONS),
            label_visibility="collapsed",
            key="hopes_slider",
        )
        st.markdown("**I have hope in AI Agents because...**")
        hopes_text = st.text_area("Hope description", value=st.session_state.hopes_text, height=100, placeholder="Write your hopes here", label_visibility="collapsed", key="hopes_input")
        st.markdown(f"**{len(hopes_text)}/350 (Min. 70 characters)**")
        st.markdown("**To what extent do you believe that your AI Agents hopes are shared by most people?**")
        hopes_shared = st.select_slider(
            "Hope shared",
            options=SHARED_FREQUENCY_OPTIONS,
            value=st.session_state.hopes_shared if st.session_state.hopes_shared in SHARED_FREQUENCY_OPTIONS else "Moderately",
            label_visibility="collapsed",
            key="hopes_shared_input",
        )

    st.markdown("---")
    col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
    with col_prev:
        page3_prev = st.form_submit_button("← Previous")
    with col_next:
        page3_next = st.form_submit_button("Next →")

if page3_prev:
    go_to_page(2)
if page3_next:
    if len(fears_text.strip()) < 70:
        st.error("Fears: Please enter at least 70 characters")
    elif len(fears_text) > 350:
        st.error("Fears: Your response exceeds 350 characters")
    elif len(hopes_text.strip()) < 70:
        st.error("Hopes: Please enter at least 70 characters")
    elif len(hopes_text) > 350:
        st.error("Hopes: Your response exceeds 350 characters")
    elif not fears_shared:
        st.error("Fears: Please select how widely your fear is shared")
    elif not hopes_shared:
        st.error("Hopes: Please select how widely your hope is shared")
    else:
        st.session_state.fears_rating = option_to_rating(fears_rating, FEAR_RATING_OPTIONS)
        st.session_state.hopes_rating = option_to_rating(hopes_rating, HOPE_RATING_OPTIONS)
        st.session_state.fears_text = fears_text
        st.session_state.hopes_text = hopes_text
        st.session_state.fears_shared = fears_shared
        st.session_state.hopes_shared = hopes_shared
        go_to_page(4)
