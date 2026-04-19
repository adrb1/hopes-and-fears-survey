import streamlit as st

from survey_app.shared import bootstrap_page, get_job_roles_for_ui, get_occupation_id_for_name, go_to_page, render_view_anchor


anchor_id = bootstrap_page(1)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='max-width: 800px'>
    <h1 style='font-weight: bold; font-size: 20px;'>WE ARE EXPLORING THE DIFFERENT FEARS AND HOPES PEOPLE HAVE ABOUT AI AGENTS</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")
st.markdown(
    """
    In this survey, you will be asked to:

    - Task 1: Share your fears and hopes about AI Agents.
    - Task 2: Explore a Task Automation Gallery showing how AI agents may support or replace parts of your work.
    - Task 3: Provide a brief evaluation of the visualization.

    All questions in this survey are mandatory. Read each of them thoroughly and provide your responses to the best of your ability.
    Copying responses from external sources is not permitted and disabled.
    """
)
st.markdown("---")

job_roles = get_job_roles_for_ui()
job_role_options = [""] + job_roles
job_role_index = job_role_options.index(st.session_state.job_role) if st.session_state.job_role in job_role_options else 0

with st.form("page1_form"):
    st.markdown("**Please enter your Prolific ID**")
    prolific_id = st.text_input("Prolific ID", value=st.session_state.prolific_id, key="prolific_input")

    st.markdown("**What is your occupation?**")
    job_role = st.selectbox(
        "Select your job role:",
        job_role_options,
        index=job_role_index,
        format_func=lambda value: "Please select your job role" if value == "" else value,
        key="job_input",
    )

    col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
    with col_prev:
        page1_prev = st.form_submit_button("← Previous")
    with col_next:
        page1_next = st.form_submit_button("Next →")

if page1_prev:
    go_to_page(0)
if page1_next:
    if not prolific_id.strip():
        st.error("Please enter your Prolific ID")
    elif not job_role:
        st.error("Please select your job role")
    else:
        st.session_state.prolific_id = prolific_id
        st.session_state.job_role = job_role
        st.session_state.participant_id = None
        st.session_state.selected_occupation_id = get_occupation_id_for_name(job_role)
        st.session_state.profile_data = {}
        st.session_state.before_attitude_data = {}
        st.session_state.after_attitude_data = {}
        st.session_state.occupation_fit_choice = ""
        go_to_page(2)
