import streamlit as st

from survey_app.shared import bootstrap_root_app, render_consent_page


bootstrap_root_app()
st.session_state.page = 0
render_consent_page()
