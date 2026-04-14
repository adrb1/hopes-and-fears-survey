import streamlit as st

from survey_app.shared import bootstrap_root_app, go_to_page, render_consent_page


bootstrap_root_app()
current_page = int(st.session_state.get("page", 0))

if current_page == 0:
	render_consent_page()
else:
	go_to_page(current_page)
