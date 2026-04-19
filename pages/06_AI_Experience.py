import streamlit as st

from survey_app.shared import LIKERT_SCALE_OPTIONS, OCCUPATION_FIT_OPTIONS, bootstrap_page, go_to_page, render_view_anchor


anchor_id = bootstrap_page(6)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>YOUR EXPERIENCE WITH AI AGENTS</h2>
        <p>Please rate your agreement with the following statements about your occupation and AI Agent usage.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.session_state.page6_question_index = 0

likert_options = LIKERT_SCALE_OPTIONS
likert_values = {opt: i + 1 for i, opt in enumerate(LIKERT_SCALE_OPTIONS)}

question_sections = [
    (
        "Occupation Fit",
        "Start with the description that best matches your current occupation.",
        [],
    ),
    (
        "Basic Familiarity",
        "These items focus on how well you recognize and understand AI Agent tools.",
        [
            ("I can distinguish between smart devices and non-smart devices", "smart_devices"),
            ("I do not know how AI Agent technology can help me", "ai_help"),
            ("I can identify the AI Agent technology employed in the applications and products I use", "ai_tech_id"),
        ],
    ),
    (
        "Practical Use",
        "These items focus on learning, using, and choosing AI Agent tools in work settings.",
        [
            ("I can skillfully use AI Agent applications or products to help me with my daily work", "ai_skillful"),
            ("It is usually hard for me to learn to use a new AI Agent application or product", "ai_learning"),
            ("I can use AI Agent applications or products to improve my work efficiency", "ai_efficiency"),
            ("I can evaluate the capabilities and limitations of an AI Agent application or product after using it for a while", "ai_eval"),
            ("I can choose a proper solution from various solutions provided by a smart agent", "ai_solution"),
            ("I can choose the most appropriate AI Agent application or product from a variety for a particular task", "ai_choice"),
        ],
    ),
    (
        "Responsible Use",
        "These items focus on attention, ethics, and risk awareness when using AI Agent technology.",
        [
            ("I believe AI Agent technologies are mainly developed by little squirrels", "attention_check"),
            ("I always comply with ethical principles when using AI Agent applications or products", "ethical"),
            ("I am never alert to privacy and information security issues when using AI Agent applications or products", "privacy"),
            ("I am always alert to the abuse of AI Agent technology", "ai_abuse"),
        ],
    ),
]

questions = [question for _, _, section_questions in question_sections for question in section_questions]

st.markdown("### Occupation Fit")
st.caption("Start with the description that best matches your current occupation.")
st.markdown("**Which description best fits your occupation?**")
current_occupation_fit = st.session_state.get("occupation_fit_radio", "")
occupation_fit_value = st.radio(
    "My occupation requires...",
    OCCUPATION_FIT_OPTIONS,
    index=OCCUPATION_FIT_OPTIONS.index(current_occupation_fit) if current_occupation_fit in OCCUPATION_FIT_OPTIONS else None,
    key="occupation_fit_radio",
)

question_values = {}
for section_title, section_description, section_questions in question_sections[1:]:
    st.markdown("---")
    st.markdown(f"### {section_title}")
    st.caption(section_description)

    for question_text, question_key in section_questions:
        display_text = question_text
        if question_key == "attention_check":
            display_text = "⚠️ " + display_text
        st.markdown(f"**{display_text}**")
        question_values[question_key] = st.select_slider(
            question_key,
            options=likert_options,
            value=st.session_state[question_key] if st.session_state[question_key] in likert_options else "Neutral",
            label_visibility="collapsed",
            key=f"{question_key}_slider",
        )

st.markdown("---")
col_prev, _, col_next = st.columns([0.2, 0.65, 0.15])
with col_prev:
    page6_prev = st.button("← Previous")
with col_next:
    page6_next = st.button("Next →")

if page6_prev:
    go_to_page(5)

if page6_next:
    if not occupation_fit_value:
        st.error("Please select the description that best fits your occupation")
        st.stop()

    missing_answer = next((question_text for question_text, question_key in questions if not question_values[question_key]), None)
    if missing_answer:
        st.error(f"Please answer: {missing_answer}")
        st.stop()

    st.session_state.occupation_fit_choice = occupation_fit_value

    if likert_values[question_values["attention_check"]] >= 3:
        st.error("⚠️ Attention check: Your response to the AI Agent squirrels question suggests you may not be answering carefully. Please review your responses.")
        st.stop()

    st.session_state.pair_index = 0
    go_to_page(7)
