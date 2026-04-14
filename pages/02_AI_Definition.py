import streamlit as st

from survey_app.shared import AI_AGENT_DEFINITION, bootstrap_page, go_to_page, render_view_anchor


anchor_id = bootstrap_page(2)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='max-width: 800px'>
    <h1 style='font-weight: bold; font-size: 18px;'>THANK YOU FOR YOUR PERSPECTIVE. FOR THIS STUDY, WE'RE USING THE FOLLOWING DEFINITION OF AI AGENTS:</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info("⚠️ UPDATE: Agent definition to be displayed here")
st.markdown("---")
st.markdown("**[AI Agent Definition]**")
st.markdown(AI_AGENT_DEFINITION)
st.markdown("---")
st.markdown("**How would you describe Artificial Intelligence (AI) Agents to a friend?**")

with st.form("page2_form"):
    ai_description = st.text_area(
        "AI description",
        value=st.session_state.ai_description,
        height=120,
        placeholder="Enter your description here...",
        key="ai_desc_input",
    )

    st.markdown(f"**{len(ai_description)}/350 (Min. 70 characters)**")

    col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
    with col_prev:
        page2_prev = st.form_submit_button("← Previous")
    with col_next:
        page2_next = st.form_submit_button("Next →")

if page2_prev:
    go_to_page(1)
if page2_next:
    if len(ai_description.strip()) < 70:
        st.error("Please enter at least 70 characters")
    elif len(ai_description) > 350:
        st.error("Your response exceeds 350 characters")
    else:
        st.session_state.ai_description = ai_description
        go_to_page(3)
