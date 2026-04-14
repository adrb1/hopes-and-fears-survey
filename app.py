import streamlit as st

from survey_app.shared import PAGE_PATHS, bootstrap_root_app


bootstrap_root_app()

navigation = st.navigation(
	[
		st.Page(PAGE_PATHS[0], title="Consent", default=True),
		st.Page(PAGE_PATHS[1], title="Identity"),
		st.Page(PAGE_PATHS[2], title="AI Definition"),
		st.Page(PAGE_PATHS[3], title="Fears and Hopes Before"),
		st.Page(PAGE_PATHS[4], title="Task Gallery"),
		st.Page(PAGE_PATHS[5], title="Demographics"),
		st.Page(PAGE_PATHS[6], title="AI Experience"),
		st.Page(PAGE_PATHS[7], title="Task Pairs"),
		st.Page(PAGE_PATHS[8], title="Fears and Hopes After"),
		st.Page(PAGE_PATHS[9], title="Completion"),
	],
	position="hidden",
)
navigation.run()
