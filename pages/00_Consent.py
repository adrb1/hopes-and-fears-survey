import streamlit as st

from survey_app.shared import bootstrap_page, components, go_to_page, render_view_anchor


anchor_id = bootstrap_page(0)
render_view_anchor(anchor_id)

st.markdown(
    """
    <div style='max-width: 900px'>
    <h1 style='font-weight: bold; font-size: 24px;'>Participant Information and Consent Form</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div id='hf-consent-scrollbox' style='max-height: 360px; overflow-y: auto; border: 1px solid #d1d5db; border-radius: 8px; padding: 16px 18px; background: #ffffff;'>
<h4 style='margin-top:0;'>GENERAL INFORMATION</h4>
<p>You are invited to participate in a research study examining how people feel about AI agents and make decisions about delegating workplace tasks to agents. The aim of this study is to better understand which tasks individuals prefer to retain and which they are willing to delegate to AI, in order to inform responsible AI adoption in professional settings.</p>

<h4>PROCEDURE</h4>
<p>Participation involves completing an online survey, which will take approximately 10-15 minutes.</p>
<p>During the survey, you will be asked to:</p>
<ul>
<li>Briefly describe your hopes and concerns regarding the use of AI in the workplace.</li>
<li>Review short descriptions of AI capabilities related to tasks in your occupation, to ensure a shared understanding of what AI systems can do.</li>
<li>Compare pairs of workplace tasks and indicate which you would prefer to perform yourself if AI could perform both tasks equally well.</li>
<li>Answer a small number of background questions (e.g. age, gender, country, education, and profession).</li>
</ul>
<p>The study is designed to examine how individuals form preferences about task delegation to AI under different informational conditions.</p>

<h4>RISKS AND BENEFITS</h4>
<p><strong>Risks:</strong> This study does not involve physical or medical risks. However, as with any online survey, there is a minimal risk related to data privacy. Appropriate safeguards are in place to minimise this risk.</p>
<p><strong>Benefits:</strong> There is no direct personal benefit from participation. However, the study contributes to research on AI and work, and may inform policies and organisational practices related to responsible AI use.</p>

<h4>CONFIDENTIALITY AND DATA PROTECTION</h4>
<p>Your responses will be pseudonymised and stored securely in accordance with the General Data Protection Regulation (GDPR).</p>
<ul>
<li>No directly identifying personal information will be collected.</li>
<li>Data will be analysed in aggregated form and cannot be traced back to individual participants.</li>
<li>Data will be stored on secure servers at the Technical University of Munich (TUM) and accessed only by authorised researchers.</li>
</ul>

<h4>VOLUNTARY PARTICIPATION</h4>
<p>Participation in this study is entirely voluntary. You may withdraw at any time without providing a reason and without any penalty. If you choose to withdraw, your data will not be used where possible.</p>

<h4>COMPENSATION</h4>
<p>Participants will receive a fixed payment via the Prolific platform upon successful completion of the survey. No compensation will be provided for incomplete participation.</p>

<h4>CONTACT INFORMATION</h4>
<p>If you have any questions or concerns about this study, please contact: <strong>dalia.ali@tum.de</strong></p>

<h4>CONSENT</h4>
<p>By proceeding with the survey, you confirm that:</p>
<ul>
<li>You have read and understood the information provided above.</li>
<li>You are at least 18 years old.</li>
<li>You voluntarily agree to participate in this study.</li>
</ul>
</div>
<p id='hf-consent-scroll-hint' style='margin-top:8px; color:#6b7280;'>Please scroll to the bottom to enable the consent checkboxes.</p>
""",
    unsafe_allow_html=True,
)

st.markdown("---")
with st.form("page0_form"):
    consent_read = st.checkbox("I have read and understood the information provided above.", key="consent_read")
    consent_age = st.checkbox("I confirm that I am at least 18 years old.", key="consent_age")
    consent_participate = st.checkbox("I voluntarily agree to participate in this study.", key="consent_participate")

    _, col_start = st.columns([0.75, 0.25])
    with col_start:
        consent_next = st.form_submit_button("Proceed to survey →")

if consent_next:
    if consent_read and consent_age and consent_participate:
        go_to_page(1)
    else:
        st.error("Please tick all consent boxes before proceeding.")

components.html(
    """
    <script>
    (function () {
        const doc = window.parent.document;
        if (!doc) return;

        const checkboxLabels = [
            "I have read and understood the information provided above.",
            "I confirm that I am at least 18 years old.",
            "I voluntarily agree to participate in this study."
        ];

        function findCheckboxByLabelText(text) {
            const labelNodes = Array.from(doc.querySelectorAll("label"));
            for (const label of labelNodes) {
                const content = (label.innerText || "").trim();
                if (content.includes(text)) {
                    const input = label.querySelector("input[type='checkbox']");
                    if (input) return input;
                }
            }
            return null;
        }

        function setEnabled(el, enabled) {
            if (!el) return;
            el.disabled = !enabled;
            const wrapper = el.closest("label");
            if (wrapper) {
                wrapper.style.opacity = enabled ? "1" : "0.55";
                wrapper.style.cursor = enabled ? "pointer" : "not-allowed";
            }
        }

        function applyLockState(unlocked) {
            checkboxLabels.forEach((text) => {
                setEnabled(findCheckboxByLabelText(text), unlocked);
            });
            const hint = doc.getElementById("hf-consent-scroll-hint");
            if (hint) {
                hint.textContent = unlocked
                    ? "Consent options are now enabled."
                    : "Please scroll to the bottom to enable the consent checkboxes.";
            }
        }

        function init() {
            const box = doc.getElementById("hf-consent-scrollbox");
            if (!box) return false;

            const atBottom = () => box.scrollTop + box.clientHeight >= box.scrollHeight - 4;

            applyLockState(atBottom());
            box.addEventListener("scroll", () => applyLockState(atBottom()), { passive: true });
            return true;
        }

        let tries = 0;
        const timer = setInterval(() => {
            tries += 1;
            if (init() || tries > 60) clearInterval(timer);
        }, 100);
    })();
    </script>
    """,
    height=0,
)
