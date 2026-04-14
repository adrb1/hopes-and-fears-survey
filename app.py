import streamlit as st

from survey_app.shared import bootstrap_root_app, go_to_page


bootstrap_root_app()
go_to_page(int(st.session_state.get("page", 0)))
