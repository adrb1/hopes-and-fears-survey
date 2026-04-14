import streamlit as st

from survey_app.shared import bootstrap_page, render_view_anchor


anchor_id = bootstrap_page(9)
render_view_anchor(anchor_id)

if st.session_state.final_submit_error:
    st.error(f"Submission status: failed ({st.session_state.final_submit_error})")
elif st.session_state.final_submit_done:
    st.success("Submission status: successfully stored in database.")

st.markdown(
    """
    <div style='text-align: center; margin-top: 100px;'>
        <h2 style='font-weight: bold;'>Thank you!</h2>
        <p>Your responses have been recorded successfully.</p>
        <p>Please close this tab or wait while we redirect you.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
