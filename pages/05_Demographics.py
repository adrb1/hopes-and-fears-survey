import streamlit as st

from survey_app.shared import AGE_GROUP_OPTIONS, bootstrap_page, go_to_page, render_view_anchor


anchor_id = bootstrap_page(5)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US ABOUT YOURSELF</h2>
        <p>Please provide a few demographic details so we can better understand participant background.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

age_options = [""] + AGE_GROUP_OPTIONS
gender_options = ["", "Female", "Male", "Nonbinary", "Transgender", "Other"]
ethnicity_options = ["", "American Indian or Alaska Native", "Asian or Pacific Islander", "Black or African American", "Hispanic or Latinx", "Middle Eastern or North African", "White", "Multiethnic", "Other"]
colour_options = ["", "Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"]
education_options = ["", "Less than High School", "High School", "Some college (no degree)", "Technical Certification", "Associate degree (2-year)", "Bachelor's degree (4-year)", "Master's degree", "Doctoral degree", "Professional degree (JD, MD)", "Other"]

with st.form("page5_form"):
    age_group = st.selectbox("What is your age group?", age_options, index=age_options.index(st.session_state.age_group) if st.session_state.age_group in age_options else 0, format_func=lambda value: "Please select" if value == "" else value, key="age_group")
    gender_selected = st.selectbox("What is your gender identity?", gender_options, index=gender_options.index(st.session_state.gender_identity) if st.session_state.gender_identity in gender_options else 0, format_func=lambda value: "Please select" if value == "" else value, key="gender_identity")
    gender_other = ""
    if gender_selected == "Other":
        gender_other = st.text_input("Please specify", value=st.session_state.gender_other, key="gender_other")

    ethnicity_selected = st.selectbox("Which ethnicity best describes you?", ethnicity_options, index=ethnicity_options.index(st.session_state.ethnicity) if st.session_state.ethnicity in ethnicity_options else 0, format_func=lambda value: "Please select" if value == "" else value, key="ethnicity")
    ethnicity_other = ""
    if ethnicity_selected == "Other":
        ethnicity_other = st.text_input("Please specify", value=st.session_state.ethnicity_other, key="ethnicity_other")

    favourite_colour = st.selectbox("Please choose red.", colour_options, index=colour_options.index(st.session_state.favourite_colour) if st.session_state.favourite_colour in colour_options else 0, format_func=lambda value: "Please select" if value == "" else value, key="favourite_colour")
    education_selected = st.selectbox("What is your highest level of education?", education_options, index=education_options.index(st.session_state.education_level) if st.session_state.education_level in education_options else 0, format_func=lambda value: "Please select" if value == "" else value, key="education_level")
    education_other = ""
    if education_selected == "Other":
        education_other = st.text_input("Please specify", value=st.session_state.education_other, key="education_other")

    col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
    with col_prev:
        page5_prev = st.form_submit_button("← Previous")
    with col_next:
        page5_next = st.form_submit_button("Next →")

if page5_prev:
    go_to_page(4)
if page5_next:
    if not age_group:
        st.error("Please fill out your age group")
    elif not gender_selected:
        st.error("Please fill out your gender identity")
    elif gender_selected == "Other" and not gender_other.strip():
        st.error("Please specify your gender identity")
    elif not ethnicity_selected:
        st.error("Please fill out your ethnicity")
    elif ethnicity_selected == "Other" and not ethnicity_other.strip():
        st.error("Please specify your ethnicity")
    elif not favourite_colour.strip():
        st.error("Please fill out your favourite colour")
    elif not education_selected:
        st.error("Please fill out your education level")
    elif education_selected == "Other" and not education_other.strip():
        st.error("Please specify your education level")
    else:
        st.session_state.age_group = age_group
        st.session_state.gender_identity = gender_selected
        st.session_state.gender_other = gender_other
        st.session_state.ethnicity = ethnicity_selected
        st.session_state.ethnicity_other = ethnicity_other
        st.session_state.favourite_colour = favourite_colour
        st.session_state.education_level = education_selected
        st.session_state.education_other = education_other
        go_to_page(6)
