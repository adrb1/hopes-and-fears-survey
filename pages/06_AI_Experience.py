import streamlit as st

from survey_app.shared import LIKERT_SCALE_OPTIONS, OCCUPATION_FIT_OPTIONS, bootstrap_page, go_to_page, render_view_anchor


anchor_id = bootstrap_page(6)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>YOUR EXPERIENCE WITH AI</h2>
        <p>Please rate your agreement with the following statements about your occupation and AI usage.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

likert_options = [""] + LIKERT_SCALE_OPTIONS
likert_values = {opt: i for i, opt in enumerate(LIKERT_SCALE_OPTIONS)}
page6_questions = [
    {"type": "occupation_fit", "text": "Which description best fits your occupation?", "key": "occupation_fit_radio", "options": [""] + OCCUPATION_FIT_OPTIONS},
    {"type": "likert", "text": "I can distinguish between smart devices and non-smart devices", "key": "smart_devices"},
    {"type": "likert", "text": "I do not know how AI technology can help me", "key": "ai_help"},
    {"type": "likert", "text": "I can identify the AI technology employed in the applications and products I use", "key": "ai_tech_id"},
    {"type": "likert", "text": "I can skillfully use AI applications or products to help me with my daily work", "key": "ai_skillful"},
    {"type": "likert", "text": "It is usually hard for me to learn to use a new AI application or product", "key": "ai_learning"},
    {"type": "likert", "text": "I can use AI applications or products to improve my work efficiency", "key": "ai_efficiency"},
    {"type": "likert", "text": "I can evaluate the capabilities and limitations of an AI application or product after using it for a while", "key": "ai_eval"},
    {"type": "likert", "text": "I can choose a proper solution from various solutions provided by a smart agent", "key": "ai_solution"},
    {"type": "likert", "text": "I believe AI technologies are mainly developed by little squirrels", "key": "attention_check"},
    {"type": "likert", "text": "I can choose the most appropriate AI application or product from a variety for a particular task", "key": "ai_choice"},
    {"type": "likert", "text": "I always comply with ethical principles when using AI applications or products", "key": "ethical"},
    {"type": "likert", "text": "I am never alert to privacy and information security issues when using AI applications or products", "key": "privacy"},
    {"type": "likert", "text": "I am always alert to the abuse of AI technology", "key": "ai_abuse"},
]

st.session_state.page6_total_questions = len(page6_questions)
idx = st.session_state.page6_question_index
current_question = page6_questions[idx]

with st.form("page6_form"):
    st.markdown(f"**Question {idx + 1}/{len(page6_questions)}**")
    current_value = None
    if current_question["type"] == "occupation_fit":
        st.markdown(f"**{current_question['text']}**")
        current_value = st.selectbox("Select the best fit:", current_question["options"], index=current_question["options"].index(st.session_state.get("occupation_fit_radio", "")) if st.session_state.get("occupation_fit_radio", "") in current_question["options"] else 0, format_func=lambda value: "Please select" if value == "" else value, key="occupation_fit_radio")
    else:
        display_text = current_question["text"]
        if current_question["key"] == "attention_check":
            display_text = "⚠️ " + display_text
        st.markdown(f"**{display_text}**")
        current_value = st.select_slider("", options=likert_options, value=st.session_state[current_question["key"]] if st.session_state[current_question["key"]] in likert_options else "", label_visibility="collapsed", key=f"{current_question['key']}_slider")

    st.markdown("---")
    col_prev, _, col_next = st.columns([0.2, 0.6, 0.2])
    with col_prev:
        page6_prev = st.form_submit_button("← Previous")
    with col_next:
        page6_next = st.form_submit_button("Finish →" if idx == len(page6_questions) - 1 else "Next →")

if page6_prev:
    if idx > 0:
        st.session_state.page6_question_index = idx - 1
        st.rerun()
    go_to_page(5)

if page6_next:
    if current_question["type"] == "occupation_fit":
        if not current_value:
            st.error("Please select the description that best fits your occupation")
            st.stop()
    else:
        st.session_state[current_question["key"]] = current_value
        if not current_value:
            st.error("Please select one option before continuing")
            st.stop()
    if idx < len(page6_questions) - 1:
        st.session_state.page6_question_index = idx + 1
        st.rerun()
    if likert_values[st.session_state["attention_check"]] >= 2:
        st.error("⚠️ Attention check: Your response to the AI squirrels question suggests you may not be answering carefully. Please review your responses.")
        st.stop()
    st.session_state.pair_index = 0
    go_to_page(7)
