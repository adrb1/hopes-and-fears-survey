import os
import threading
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


PAGE_PATHS = {
    0: "pages/00_Consent.py",
    1: "pages/01_Identity.py",
    2: "pages/02_AI_Definition.py",
    3: "pages/03_Fears_Hopes_Before.py",
    4: "pages/04_Task_Gallery.py",
    5: "pages/05_Demographics.py",
    6: "pages/06_AI_Experience.py",
    7: "pages/07_Task_Pairs.py",
    8: "pages/08_Fears_Hopes_After.py",
    9: "pages/09_Completion.py",
}

DEFAULT_JOB_ROLES = [
    "Software Engineer",
    "Teacher / Educator",
    "Healthcare Professional",
    "Business Manager",
    "Marketing Professional",
    "Customer Service Representative",
    "Content Writer",
    "Graphic Designer",
    "Project Manager",
]

SHARED_FREQUENCY_OPTIONS = [
    "Not at all",
    "Rarely",
    "Occasionally",
    "Moderately",
    "Often",
    "Very often",
    "Almost always",
]

FEAR_RATING_OPTIONS = [
    "No fear at all",
    "Slight fear",
    "Moderate fear",
    "High fear",
    "Terrified",
]

HOPE_RATING_OPTIONS = [
    "No hope at all",
    "Slight hope",
    "Moderate hope",
    "High hope",
    "Full of hope",
]

LIKERT_SCALE_OPTIONS = [
    "Strongly Disagree",
    "Disagree",
    "Somewhat Disagree",
    "Neutral",
    "Somewhat Agree",
    "Agree",
    "Strongly Agree",
]

PAGE6_LIKERT_KEYS = [
    "smart_devices",
    "ai_help",
    "ai_tech_id",
    "ai_skillful",
    "ai_learning",
    "ai_efficiency",
    "ai_eval",
    "ai_solution",
    "attention_check",
    "ai_choice",
    "ethical",
    "privacy",
    "ai_abuse",
]


def rating_to_option(value, options):
    clamped_value = min(max(int(value or 1), 1), len(options))
    return options[clamped_value - 1]


def option_to_rating(value, options):
    return options.index(value) + 1

AGE_GROUP_OPTIONS = [
    "18-24 years old",
    "25-34 years old",
    "35-44 years old",
    "45-54 years old",
    "55-64 years old",
    "65+ years old",
]

OCCUPATION_FIT_OPTIONS = [
    "minimal prior experience or training, potentially needs a high school diploma or GED, and typically involves a brief training period of a few days to a few months.",
    "high school diploma, several months to a year of training, and often involve assisting others.",
    "vocational training, a college degree, or specialized certifications, and typically involves complex problem-solving, creativity, or advanced technical skills.",
]

AI_AGENT_DEFINITION = """AI Agents are systems that can plan, act, and collaborate with humans to complete digital tasks autonomously. They can analyse information, generate content, make recommendations, and communicate in natural language, often adapting their actions based on feedback or changing goals.
In this study, we're interested in your views on which of these kinds of tasks you would prefer to keep doing yourself and which you might allow an AI Agent to handle."""

MOCK_TASKS = [
    {
        "id": 1,
        "title": "Process correspondence and paperwork",
        "risk_level": "HIGH",
        "automation_level": "HIGH",
        "description": "Process all correspondence and paperwork related to accounts.",
        "capability": "Document processing and automated correspondence management systems can fully handle standardized communications, form completion, and administrative paperwork with minimal human oversight.",
        "example_tech": "AI Agent-powered CRM systems like Salesforce Einstein or HubSpot AI Agent can automatically process, categorize, and respond to routine correspondence.",
        "dimensions": ["Mental", "Individual", "Routine", "Easy"],
        "risk_analysis": "High risk due to potential errors in automated correspondence that could damage professional relationships. AI Agents may misinterpret context or tone, leading to inappropriate responses. Requires careful monitoring and human oversight for complex communications.",
    },
    {
        "id": 2,
        "title": "Generate lesson plans",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Generate lesson plans tailored to different student levels and educational needs.",
        "capability": "AI Agents can analyze curriculum standards and student data to create customized, adaptive lesson plans that cater to diverse learning styles and pace.",
        "example_tech": "AI Agent tools like ChatGPT, Google's NotebookLM, and specialized education platforms can generate structured lesson plans in minutes.",
        "dimensions": ["Mental", "Individual", "Routine", "Easy"],
        "risk_analysis": "Low risk as AI Agent-generated lesson plans can be reviewed and customized by teachers. The technology enhances efficiency while maintaining educational quality and teacher expertise.",
    },
    {
        "id": 3,
        "title": "Schedule meetings",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Schedule and coordinate meetings across teams and time zones.",
        "capability": "AI Agents can analyze calendars, preferences, and time zones to find optimal meeting times and send invitations automatically.",
        "example_tech": "Tools like Microsoft Copilot for Outlook and AI Agent scheduling assistants can automate meeting coordination.",
        "dimensions": ["Mental", "Routine", "Easy"],
        "risk_analysis": "Medium risk as scheduling conflicts or misinterpretations of availability could occur. However, most scheduling issues are recoverable and AI Agents can significantly reduce coordination overhead.",
    },
    {
        "id": 4,
        "title": "Analyze student performance",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Analyze student performance data and generate insights.",
        "capability": "AI Agents can process large datasets, identify patterns, and generate actionable insights on student learning trends and areas needing support.",
        "example_tech": "Learning analytics platforms powered by AI Agents can track progress and recommend interventions.",
        "dimensions": ["Mental", "Individual", "Easy"],
        "risk_analysis": "Low risk as AI Agent analytics provide data-driven insights that complement teacher judgment. Teachers retain final decision-making authority while benefiting from comprehensive data analysis.",
    },
    {
        "id": 5,
        "title": "Write emails",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Compose and send routine emails.",
        "capability": "AI Agents can draft professional emails based on templates and context, significantly reducing composition time.",
        "example_tech": "AI Agent writing assistants like Grammarly AI and email plugins can auto-generate email content.",
        "dimensions": ["Mental", "Routine", "Easy"],
        "risk_analysis": "Medium risk due to potential miscommunication from AI Agent-generated content. Tone, context, and nuanced language may not be perfectly captured, requiring human review for important communications.",
    },
    {
        "id": 6,
        "title": "Create content",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Create educational content, summaries, and explanations.",
        "capability": "AI Agents can generate diverse content formats from text to multimedia, adapting to different learning preferences.",
        "example_tech": "Generative AI Agent models like GPT-4 and specialized content creation tools can produce educational materials.",
        "dimensions": ["Mental", "Individual"],
        "risk_analysis": "Medium risk as AI Agent-generated content may lack depth or contain inaccuracies. Educational content requires accuracy and pedagogical expertise, so human review and customization are essential.",
    },
    {
        "id": 7,
        "title": "Grade assignments",
        "risk_level": "HIGH",
        "automation_level": "MEDIUM",
        "description": "Grade assignments and provide feedback.",
        "capability": "AI Agents can evaluate objective assessments and provide personalized feedback, though subjective work still benefits from human review.",
        "example_tech": "AI Agent-powered grading systems can score tests and essays with human-in-the-loop review.",
        "dimensions": ["Routine", "Easy"],
        "risk_analysis": "High risk due to the subjective nature of assessment and potential bias in AI Agent grading algorithms. Student grades significantly impact educational and career opportunities, requiring human judgment.",
    },
    {
        "id": 8,
        "title": "Monitor student progress",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Monitor student progress and flag concerns.",
        "capability": "Continuous AI Agent monitoring can track learning metrics and alert educators to struggling students in real-time.",
        "example_tech": "Learning management systems with AI Agent analytics provide real-time student progress monitoring.",
        "dimensions": ["Mental", "Routine"],
        "risk_analysis": "Low risk as AI Agent monitoring serves as an early warning system that enhances teacher effectiveness. Teachers can intervene based on AI Agent alerts while maintaining oversight of student development.",
    },
    {
        "id": 9,
        "title": "Content moderation",
        "risk_level": "HIGH",
        "automation_level": "HIGH",
        "description": "Moderate user-generated content and discussions.",
        "capability": "AI Agents can identify inappropriate content, spam, and policy violations across large volumes of text and media.",
        "example_tech": "Content moderation APIs and platforms use machine learning for real-time filtering.",
        "dimensions": ["Routine", "Easy"],
        "risk_analysis": "High risk due to potential false positives/negatives in content detection. Over-moderation can suppress valid expression, while under-moderation can allow harmful content. Requires careful algorithm tuning and human oversight.",
    },
    {
        "id": 10,
        "title": "Personalized tutoring",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Provide personalized tutoring and one-on-one support.",
        "capability": "AI Agent tutors can adapt to individual learning speeds, answer questions 24/7, and provide unlimited practice with feedback.",
        "example_tech": "AI Agent tutoring platforms like Carnegie Learning and Squirrel AI offer adaptive learning experiences.",
        "dimensions": ["Mental", "Individual"],
        "risk_analysis": "Low risk as AI Agent tutoring supplements rather than replaces human instruction. Students benefit from 24/7 access to practice and immediate feedback while teachers focus on complex learning needs.",
    },
    {
        "id": 11,
        "title": "Data entry",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Enter data into systems and databases.",
        "capability": "AI Agents can extract, validate, and enter data with high accuracy, reducing manual data entry errors.",
        "example_tech": "RPA tools and AI Agent OCR systems automate data entry from various sources.",
        "dimensions": ["Routine", "Easy"],
        "risk_analysis": "Low risk as data entry is highly automatable with minimal consequences for errors. AI Agents can achieve higher accuracy than manual entry while freeing humans for more valuable tasks.",
    },
    {
        "id": 12,
        "title": "Curriculum design",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Design and develop new curricula.",
        "capability": "AI Agents can assist in curriculum development by analyzing standards, suggesting best practices, and ensuring alignment.",
        "example_tech": "AI Agent curriculum tools can help map learning objectives and suggest content sequences.",
        "dimensions": ["Mental", "Individual"],
        "risk_analysis": "Medium risk as curriculum design requires deep pedagogical knowledge and cultural context. AI Agents can assist but cannot replace the expertise needed for comprehensive educational program development.",
    },
]

MOCK_PAIRS = [
    {
        "pair_id": -1,
        "left": {"task_id": 2, "title": "Generate lesson plans", "description": "Generate lesson plans tailored to different student levels."},
        "right": {"task_id": 1, "title": "Process correspondence", "description": "Process all correspondence and paperwork related to accounts."},
    },
    {
        "pair_id": -2,
        "left": {"task_id": 5, "title": "Write emails", "description": "Compose and send routine emails."},
        "right": {"task_id": 3, "title": "Schedule meetings", "description": "Schedule and coordinate meetings across teams."},
    },
    {
        "pair_id": -3,
        "left": {"task_id": 7, "title": "Grade assignments", "description": "Grade assignments and provide feedback."},
        "right": {"task_id": 4, "title": "Analyze student performance", "description": "Analyze student performance data and generate insights."},
    },
]

SESSION_DEFAULTS = {
    "page": 0,
    "participant_id": None,
    "prolific_id": "",
    "job_role": "",
    "selected_occupation_id": None,
    "job_role_other": "",
    "ai_description": "",
    "fears_rating": 3,
    "hopes_rating": 3,
    "fears_text": "",
    "hopes_text": "",
    "fears_shared": "Moderately",
    "hopes_shared": "Moderately",
    "selected_task": None,
    "page6_question_index": 0,
    "pair_index": 0,
    "pair_choices": {},
    "fears_rating_after": 3,
    "hopes_rating_after": 3,
    "fears_text_after": "",
    "hopes_text_after": "",
    "fears_shared_after": "Moderately",
    "hopes_shared_after": "Moderately",
    "last_scrolled_task_id": None,
    "detail_open_token": 0,
    "last_detail_scroll_token": -1,
    "pending_task_events": [],
    "final_submit_done": False,
    "final_submit_error": "",
    "last_view_anchor": None,
    "age_group": "",
    "gender_identity": "",
    "gender_other": "",
    "ethnicity": "",
    "ethnicity_other": "",
    "favourite_colour": "",
    "favourite_colour_other": "",
    "education_level": "",
    "education_other": "",
    "profile_data": {},
    "before_attitude_data": {},
    "after_attitude_data": {},
    "viewed_task_ids": set(),
    "occupation_fit_radio": "",
    "occupation_fit_choice": "",
    "smart_devices": "Neutral",
    "ai_help": "Neutral",
    "ai_tech_id": "Neutral",
    "ai_skillful": "Neutral",
    "ai_learning": "Neutral",
    "ai_efficiency": "Neutral",
    "ai_eval": "Neutral",
    "ai_solution": "Neutral",
    "attention_check": "Neutral",
    "ai_choice": "Neutral",
    "ethical": "Neutral",
    "privacy": "Neutral",
    "ai_abuse": "Neutral",
}


def configure_page():
    st.set_page_config(page_title="Hopes & Fears Survey", layout="centered", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
            html, body,
            [data-testid="stAppViewContainer"],
            [data-testid="stAppViewContainer"] > .main {
                scroll-behavior: auto !important;
            }
            [data-testid="stAppViewContainer"] > .main {
                max-width: 960px;
                margin: auto;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            [data-testid="collapsedControl"],
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
            [data-testid="stSlider"] .stSlider {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }
            .stSlider, .stSelectSlider {
                margin-bottom: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    components.html(
        """
        <script>
            (function () {
                const doc = window.parent.document;
                if (!doc || doc.__hfBlockCopyPasteInstalled) return;
                doc.__hfBlockCopyPasteInstalled = true;

                const isTextField = (el) => {
                    if (!el) return false;
                    if (el.tagName === "TEXTAREA") return true;
                    if (el.tagName === "INPUT") {
                        const t = (el.type || "text").toLowerCase();
                        return ["text", "search", "email", "url", "tel", "password", "number"].includes(t);
                    }
                    return el.isContentEditable === true;
                };

                const isProlificField = (el) => {
                    if (!el) return false;
                    const directAria = (el.getAttribute && el.getAttribute("aria-label")) || "";
                    if (directAria.toLowerCase().includes("prolific id")) return true;
                    const wrap = el.closest && el.closest("div[data-testid='stTextInput']");
                    if (!wrap) return false;
                    const labelText = ((wrap.querySelector("label") || {}).innerText || "").toLowerCase();
                    if (labelText.includes("prolific id")) return true;
                    const input = wrap.querySelector("input");
                    const inputAria = (input && input.getAttribute("aria-label")) || "";
                    return inputAria.toLowerCase().includes("prolific id");
                };

                const block = (e) => {
                    const field = isTextField(e.target)
                        ? e.target
                        : (isTextField(doc.activeElement) ? doc.activeElement : null);

                    if (e.type === "copy" || e.type === "cut") {
                        e.preventDefault();
                        e.stopPropagation();
                        return;
                    }

                    if (!field) return;
                    if (e.type === "paste" && isProlificField(field)) return;
                    e.preventDefault();
                    e.stopPropagation();
                };

                ["copy", "paste", "cut", "drop", "contextmenu"].forEach((evt) => {
                    doc.addEventListener(evt, block, true);
                });

                doc.addEventListener("keydown", (e) => {
                    const field = isTextField(e.target)
                        ? e.target
                        : (isTextField(doc.activeElement) ? doc.activeElement : null);
                    if (!field) return;
                    const key = (e.key || "").toLowerCase();
                    const combo = e.ctrlKey || e.metaKey;
                    const prolificPaste = isProlificField(field) && ((combo && key === "v") || (e.shiftKey && key === "insert"));
                    if (prolificPaste) return;
                    if ((combo && ["c", "v", "x", "insert"].includes(key)) || (e.shiftKey && key === "insert")) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }, true);
            })();
        </script>
        """,
        height=0,
    )


def _secret_or_env(secret_key, env_key=None, default=None):
    try:
        if secret_key in st.secrets:
            return st.secrets[secret_key]
    except Exception:
        pass
    return os.getenv(env_key or secret_key.upper(), default)


def _build_db_url_from_ssh_secrets():
    ssh_host = _secret_or_env("ssh_host")
    ssh_port = int(_secret_or_env("ssh_port", default=22))
    ssh_user = _secret_or_env("ssh_user")
    ssh_password = _secret_or_env("ssh_password")

    db_host = _secret_or_env("db_host", default="127.0.0.1")
    db_port = int(_secret_or_env("db_port", default=3306))
    db_user = _secret_or_env("db_user")
    db_password = _secret_or_env("db_password", default="")
    db_name = _secret_or_env("db_name")

    required = [ssh_host, ssh_user, ssh_password, db_user, db_name]
    if not all(required):
        return None, None

    from sshtunnel import SSHTunnelForwarder

    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_password=ssh_password,
        remote_bind_address=(db_host, db_port),
        set_keepalive=30,
    )

    error_holder = [None]

    def _start():
        try:
            tunnel.start()
        except Exception as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=_start, daemon=True)
    thread.start()
    thread.join(timeout=6)
    if thread.is_alive():
        raise TimeoutError("SSH tunnel did not connect within 6 seconds")
    if error_holder[0] is not None:
        raise error_holder[0]

    import pymysql

    def _make_conn():
        return pymysql.connect(
            host="127.0.0.1",
            port=tunnel.local_bind_port,
            user=db_user,
            password=str(db_password),
            database=db_name,
            connect_timeout=30,
        )

    engine = create_engine(
        "mysql+pymysql://",
        creator=_make_conn,
        pool_pre_ping=True,
        pool_recycle=600,
    )
    return engine, tunnel


@st.cache_resource(show_spinner=False)
def init_db_connection():
    db_mode = "sqlite"
    db_url = "sqlite:///./survey.db"
    tunnel = None
    db_config_error = None
    ssh_engine = None

    try:
        ssh_engine, ssh_tunnel = _build_db_url_from_ssh_secrets()
        if ssh_engine is not None:
            tunnel = ssh_tunnel
            db_url = "mysql+pymysql://"
            db_mode = "ssh_tunnel"
        else:
            secrets_db_url = None
            try:
                if "DB_URL" in st.secrets:
                    secrets_db_url = st.secrets["DB_URL"]
                elif "database" in st.secrets and "url" in st.secrets["database"]:
                    secrets_db_url = st.secrets["database"]["url"]
            except Exception:
                pass

            env_db_url = os.getenv("DB_URL") or os.getenv("HOPES_FEARS_DB_URL")
            if secrets_db_url or env_db_url:
                db_url = secrets_db_url or env_db_url
                db_mode = "db_url"
    except Exception as exc:
        db_config_error = str(exc).splitlines()[0]
        db_mode = "sqlite_fallback"
        db_url = "sqlite:///./survey.db"

    if ssh_engine is not None:
        engine = ssh_engine
    else:
        is_sqlite = db_url.startswith("sqlite")
        engine = create_engine(
            db_url,
            pool_pre_ping=not is_sqlite,
            connect_args={"check_same_thread": False} if is_sqlite else {},
        )
    return engine, db_url, db_mode, db_config_error, tunnel


engine, DB_URL, DB_MODE, DB_CONFIG_ERROR, DB_TUNNEL = init_db_connection()
IS_SQLITE = DB_URL.startswith("sqlite")
DB_INIT_ERROR = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Occupation(Base):
    __tablename__ = "occupations"

    occupation_id = Column(Integer, primary_key=True, autoincrement=True)
    occupation_name = Column(String(150), unique=True, nullable=False)
    definition_text = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    tasks = relationship("OccupationTask", back_populates="occupation")


class OccupationTask(Base):
    __tablename__ = "occupation_tasks"

    task_id = Column(BigInteger, primary_key=True, autoincrement=True)
    occupation_id = Column(Integer, ForeignKey("occupations.occupation_id"), nullable=False)
    task_name = Column(String(255), nullable=False)
    task_description = Column(Text)
    color_code = Column(Enum("red", "yellow", "green", name="color_code_enum"), nullable=False)
    exposure_label = Column(String(100))
    mp_label = Column(String(100))
    td_label = Column(String(100))
    vr_label = Column(String(100))
    eh_label = Column(String(100))
    justification = Column(Text)
    task_order = Column(Integer)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    occupation = relationship("Occupation", back_populates="tasks")


class TasksImport(Base):
    __tablename__ = "tasks_import"
    employment_role = Column(String(255))
    task_name = Column(Text)
    exposure = Column(String(5))
    mp = Column(String(5))
    td = Column(String(5))
    vr = Column(String(5))
    eh = Column(String(5))
    justification = Column(Text)
    __mapper_args__ = {
        "primary_key": [employment_role, task_name, exposure, mp, td, vr, eh, justification]
    }


class Participant(Base):
    __tablename__ = "participants"
    participant_id = Column(BigInteger, primary_key=True, autoincrement=True)
    prolific_id = Column(String(100), unique=True, nullable=False)
    occupation_id = Column(Integer, ForeignKey("occupations.occupation_id"), nullable=False)
    entry_date = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    profile = relationship("ParticipantProfile", uselist=False, back_populates="participant")
    attitudes = relationship("ParticipantAttitudes", back_populates="participant")
    gallery_events = relationship("ParticipantTaskGalleryEvents", back_populates="participant")
    ai_behavior = relationship("ParticipantAIBehavior", uselist=False, back_populates="participant")


class ParticipantProfile(Base):
    __tablename__ = "participant_profile"
    profile_id = Column(BigInteger, primary_key=True, autoincrement=True)
    participant_id = Column(BigInteger, ForeignKey("participants.participant_id"), unique=True, nullable=False)
    age_group = Column(
        Enum(
            *AGE_GROUP_OPTIONS,
            name="participant_profile_age_group_enum",
        )
    )
    gender_identity = Column(String(100))
    ethnicity = Column(String(150))
    favourite_colour = Column(String(50))
    education_level = Column(String(150))
    occupation_description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    participant = relationship("Participant", back_populates="profile")


class ParticipantAttitudes(Base):
    __tablename__ = "participant_attitudes"
    attitude_id = Column(BigInteger, primary_key=True, autoincrement=True)
    participant_id = Column(BigInteger, ForeignKey("participants.participant_id"), nullable=False)
    phase = Column(Enum("before", "after", name="participant_attitudes_phase_enum"), nullable=False)
    ai_description = Column(Text)
    fear_rating = Column(SmallInteger)
    fear_text = Column(Text)
    fear_shared_rating = Column(SmallInteger)
    hope_rating = Column(SmallInteger)
    hope_text = Column(Text)
    hope_shared_rating = Column(SmallInteger)
    fear_rating_after = Column(SmallInteger)
    fear_text_after = Column(Text)
    fear_shared_rating_after = Column(SmallInteger)
    hope_rating_after = Column(SmallInteger)
    hope_text_after = Column(Text)
    hope_shared_rating_after = Column(SmallInteger)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    participant = relationship("Participant", back_populates="attitudes")


class ParticipantTaskGalleryEvents(Base):
    __tablename__ = "participant_task_gallery_events"
    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    participant_id = Column(BigInteger, ForeignKey("participants.participant_id"), nullable=False)
    task_id = Column(BigInteger, ForeignKey("occupation_tasks.task_id"), nullable=False)
    event_type = Column(Enum("view", "open_more", "close", "hover", name="participant_task_gallery_events_event_type_enum"), nullable=False)
    event_time = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    participant = relationship("Participant", back_populates="gallery_events")


class ParticipantAIBehavior(Base):
    __tablename__ = "participant_ai_scale"
    participant_id = Column(BigInteger, ForeignKey("participants.participant_id"), primary_key=True, nullable=False)
    ai_familiarity = Column(SmallInteger)
    ai_comfort = Column(SmallInteger)
    ai_use_frequency = Column(SmallInteger)
    ai_trust = Column(SmallInteger)
    agent_confidence = Column(SmallInteger)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    participant = relationship("Participant", back_populates="ai_behavior")


class TaskPairs(Base):
    __tablename__ = "task_pairs"
    pair_id = Column(BigInteger, primary_key=True, autoincrement=True)
    occupation_id = Column(Integer, ForeignKey("occupations.occupation_id"), nullable=False)
    left_task_id = Column(BigInteger, ForeignKey("occupation_tasks.task_id"), nullable=False)
    right_task_id = Column(BigInteger, ForeignKey("occupation_tasks.task_id"), nullable=False)
    pair_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))


class ParticipantTaskPairChoices(Base):
    __tablename__ = "participant_task_pair_choices"
    choice_id = Column(BigInteger, primary_key=True, autoincrement=True)
    participant_id = Column(BigInteger, ForeignKey("participants.participant_id"), nullable=False)
    pair_id = Column(BigInteger, ForeignKey("task_pairs.pair_id"), nullable=False)
    choice_made = Column(Enum("left", "right", "skip", name="participant_task_pair_choices_choice_made_enum"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))


def ensure_participant_attitudes_after_columns():
    if DB_INIT_ERROR is not None:
        return

    required_columns = {
        "fear_rating_after": "SMALLINT",
        "fear_text_after": "TEXT",
        "fear_shared_rating_after": "SMALLINT",
        "hope_rating_after": "SMALLINT",
        "hope_text_after": "TEXT",
        "hope_shared_rating_after": "SMALLINT",
    }

    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("participant_attitudes")}
    missing_columns = [(name, col_type) for name, col_type in required_columns.items() if name not in existing_columns]

    if not missing_columns:
        return

    with engine.begin() as conn:
        for col_name, col_type in missing_columns:
            conn.execute(text(f"ALTER TABLE participant_attitudes ADD COLUMN {col_name} {col_type}"))


def ensure_participant_profile_age_group_enum():
    if DB_INIT_ERROR is not None:
        return

    desired_enum = ", ".join(f"'{value}'" for value in AGE_GROUP_OPTIONS)
    with engine.begin() as conn:
        conn.execute(
            text(
                f"ALTER TABLE participant_profile MODIFY COLUMN age_group ENUM({desired_enum}) NULL"
            )
        )


@st.cache_resource(show_spinner=False)
def initialize_database_schema():
    Base.metadata.create_all(bind=engine)
    ensure_participant_attitudes_after_columns()
    ensure_participant_profile_age_group_enum()


try:
    initialize_database_schema()
except Exception as exc:
    DB_INIT_ERROR = str(exc).splitlines()[0]


def ensure_session_state():
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            if isinstance(value, dict):
                st.session_state[key] = dict(value)
            elif isinstance(value, list):
                st.session_state[key] = list(value)
            else:
                st.session_state[key] = value

    for key in PAGE6_LIKERT_KEYS:
        if st.session_state.get(key) not in LIKERT_SCALE_OPTIONS:
            st.session_state[key] = "Neutral"

    for key in ["fears_shared", "hopes_shared", "fears_shared_after", "hopes_shared_after"]:
        if st.session_state.get(key) not in SHARED_FREQUENCY_OPTIONS:
            st.session_state[key] = "Moderately"

    # Clear stale values from older app versions so final submission never writes an invalid enum.
    if st.session_state.get("age_group") not in ["", *AGE_GROUP_OPTIONS]:
        st.session_state.age_group = ""


def get_page_path(page_number):
    return PAGE_PATHS[page_number]


def go_to_page(page_number):
    st.session_state.page = page_number
    st.switch_page(get_page_path(page_number))


def bootstrap_root_app():
    configure_page()
    ensure_session_state()


def render_consent_page():
    anchor_id = _apply_view_anchor_behavior(0)
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
<p>You are invited to participate in a research study examining how people feel about AI Agents and make decisions about delegating workplace tasks to agents. The aim of this study is to better understand which tasks individuals prefer to retain and which they are willing to delegate to AI Agents, in order to inform responsible AI Agent adoption in professional settings.</p>

<h4>PROCEDURE</h4>
<p>Participation involves completing an online survey, which will take approximately 10-15 minutes.</p>
<p>During the survey, you will be asked to:</p>
<ul>
<li>Briefly describe your hopes and concerns regarding the use of AI Agents in the workplace.</li>
<li>Review short descriptions of AI Agent capabilities related to tasks in your occupation, to ensure a shared understanding of what AI Agent systems can do.</li>
<li>Compare pairs of workplace tasks and indicate which you would prefer to perform yourself if AI Agents could perform both tasks equally well.</li>
<li>Answer a small number of background questions (e.g. age, gender, country, education, and profession).</li>
</ul>
<p>The study is designed to examine how individuals form preferences about task delegation to AI Agents under different informational conditions.</p>

<h4>RISKS AND BENEFITS</h4>
<p><strong>Risks:</strong> This study does not involve physical or medical risks. However, as with any online survey, there is a minimal risk related to data privacy. Appropriate safeguards are in place to minimise this risk.</p>
<p><strong>Benefits:</strong> There is no direct personal benefit from participation. However, the study contributes to research on AI Agents and work, and may inform policies and organisational practices related to responsible AI Agent use.</p>

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


def _get_view_anchor(page_number):
    return (
        page_number,
        st.session_state.page6_question_index if page_number == 6 else None,
        st.session_state.pair_index if page_number == 7 else None,
    )


def get_view_anchor_id(page_number):
    anchor = _get_view_anchor(page_number)
    return f"hf-view-anchor-{anchor[0]}-{anchor[1]}-{anchor[2]}"


def _apply_view_anchor_behavior(page_number):
    current_anchor = _get_view_anchor(page_number)
    anchor_id = get_view_anchor_id(page_number)
    if st.session_state.last_view_anchor is None:
        st.session_state.last_view_anchor = current_anchor
    elif st.session_state.last_view_anchor != current_anchor:
        components.html(
            """
            <script>
                (function () {
                    const anchorId = "__ANCHOR__";
                    const w = window.parent;
                    const doc = w.document;

                    function scrollToAnchor() {
                        const anchor = doc.getElementById(anchorId);
                        if (!anchor) return false;
                        anchor.scrollIntoView({ block: "start", inline: "nearest", behavior: "auto" });
                        return true;
                    }

                    function goTopFallback() {
                        w.scrollTo({ top: 0, left: 0, behavior: "auto" });
                        const main = doc.querySelector("[data-testid='stAppViewContainer'] > .main");
                        if (main) main.scrollTop = 0;
                    }

                    function applyAnchor() {
                        if (!scrollToAnchor()) goTopFallback();
                    }

                    requestAnimationFrame(applyAnchor);
                    setTimeout(applyAnchor, 60);
                })();
            </script>
            """.replace("__ANCHOR__", anchor_id),
            height=0,
        )
        st.session_state.last_view_anchor = current_anchor
    return anchor_id


def render_view_anchor(anchor_id):
    st.markdown(
        f"<div id='{anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>",
        unsafe_allow_html=True,
    )


def bootstrap_page(page_number):
    configure_page()
    ensure_session_state()
    st.session_state.page = page_number
    anchor_id = _apply_view_anchor_behavior(page_number)
    if page_number >= 1:
        render_runtime_status_banner(page_number)
    return anchor_id


def get_or_create_occupation(db, occupation_name):
    occ = db.query(Occupation).filter(Occupation.occupation_name == occupation_name).first()
    if not occ:
        occ = Occupation(occupation_name=occupation_name, definition_text="", is_active=True)
        db.add(occ)
        db.flush()
    return occ


def get_occupation_id_for_name(occupation_name):
    normalized_name = (occupation_name or "").strip()
    if not normalized_name:
        return None

    db = SessionLocal()
    try:
        return db.query(Occupation.occupation_id).filter(Occupation.occupation_name == normalized_name).scalar()
    finally:
        db.close()


def get_or_create_participant(db, prolific_id, occupation_name=None, occupation_id=None, commit=True):
    participant = db.query(Participant).filter(Participant.prolific_id == prolific_id).first()
    resolved_occupation_id = occupation_id
    if resolved_occupation_id is None:
        occ = get_or_create_occupation(db, occupation_name)
        resolved_occupation_id = occ.occupation_id

    if not participant:
        participant = Participant(prolific_id=prolific_id, occupation_id=resolved_occupation_id, entry_date=datetime.utcnow())
        db.add(participant)
        db.flush()
    else:
        participant.occupation_id = resolved_occupation_id

    if commit:
        db.commit()
    return participant.participant_id


def get_ai_agent_definition_for_occupation_id(occupation_id):
    if not occupation_id:
        return AI_AGENT_DEFINITION

    db = SessionLocal()
    try:
        definition_text = (
            db.query(Occupation.definition_text)
            .filter(Occupation.occupation_id == occupation_id)
            .scalar()
        )
    finally:
        db.close()

    normalized_definition = (definition_text or "").strip()
    return normalized_definition or AI_AGENT_DEFINITION


def resolve_participant_id_for_submission(db, prolific_id, occupation_name, occupation_id=None):
    session_participant_id = st.session_state.get("participant_id")
    if session_participant_id:
        existing_participant = db.query(Participant).filter(Participant.participant_id == session_participant_id).first()
        if existing_participant and existing_participant.prolific_id == prolific_id:
            if occupation_id is not None:
                existing_participant.occupation_id = occupation_id
            return existing_participant.participant_id

    participant_id = get_or_create_participant(
        db,
        prolific_id,
        occupation_name=occupation_name,
        occupation_id=occupation_id,
        commit=False,
    )
    st.session_state.participant_id = participant_id
    return participant_id


def save_profile(db, participant_id, commit=True, **kwargs):
    existing_profile_id = db.query(ParticipantProfile.profile_id).filter(
        ParticipantProfile.participant_id == participant_id
    ).scalar()

    update_values = {}
    fields = [
        "age_group",
        "gender_identity",
        "ethnicity",
        "favourite_colour",
        "education_level",
        "occupation_description",
    ]
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            update_values[field] = kwargs[field]

    update_values["created_at"] = datetime.utcnow()

    if existing_profile_id is None:
        db.add(ParticipantProfile(participant_id=participant_id, **update_values))
    elif update_values:
        db.query(ParticipantProfile).filter(ParticipantProfile.participant_id == participant_id).update(
            update_values,
            synchronize_session=False,
        )

    if commit:
        db.commit()


def get_profile_submission_data():
    stored_profile = st.session_state.get("profile_data") or {}

    age_group = stored_profile.get("age_group", st.session_state.get("age_group"))
    gender_identity = stored_profile.get("gender_identity", st.session_state.get("gender_identity"))
    ethnicity = stored_profile.get("ethnicity", st.session_state.get("ethnicity"))
    favourite_colour = stored_profile.get("favourite_colour", st.session_state.get("favourite_colour"))
    education_level = stored_profile.get("education_level", st.session_state.get("education_level"))

    normalized_profile = {
        "age_group": age_group if age_group in AGE_GROUP_OPTIONS else None,
        "gender_identity": (gender_identity or "").strip(),
        "ethnicity": (ethnicity or "").strip(),
        "favourite_colour": (favourite_colour or "").strip(),
        "education_level": (education_level or "").strip(),
    }

    return normalized_profile


def get_occupation_fit_submission_data():
    stored_choice = (st.session_state.get("occupation_fit_choice") or "").strip()
    widget_choice = (st.session_state.get("occupation_fit_radio") or "").strip()
    final_choice = stored_choice or widget_choice

    if final_choice not in OCCUPATION_FIT_OPTIONS:
        return None

    return final_choice


def get_before_attitude_submission_data():
    stored_payload = st.session_state.get("before_attitude_data") or {}

    return {
        "fears_rating": stored_payload.get("fears_rating", st.session_state.get("fears_rating")),
        "fears_text": stored_payload.get("fears_text", st.session_state.get("fears_text")),
        "fears_shared": stored_payload.get("fears_shared", st.session_state.get("fears_shared")),
        "hopes_rating": stored_payload.get("hopes_rating", st.session_state.get("hopes_rating")),
        "hopes_text": stored_payload.get("hopes_text", st.session_state.get("hopes_text")),
        "hopes_shared": stored_payload.get("hopes_shared", st.session_state.get("hopes_shared")),
    }


def get_after_attitude_submission_data():
    stored_payload = st.session_state.get("after_attitude_data") or {}

    return {
        "fears_rating_after": stored_payload.get("fears_rating_after", st.session_state.get("fears_rating_after")),
        "fears_text_after": stored_payload.get("fears_text_after", st.session_state.get("fears_text_after")),
        "fears_shared_after": stored_payload.get("fears_shared_after", st.session_state.get("fears_shared_after")),
        "hopes_rating_after": stored_payload.get("hopes_rating_after", st.session_state.get("hopes_rating_after")),
        "hopes_text_after": stored_payload.get("hopes_text_after", st.session_state.get("hopes_text_after")),
        "hopes_shared_after": stored_payload.get("hopes_shared_after", st.session_state.get("hopes_shared_after")),
    }


def _sharing_index(value):
    return SHARED_FREQUENCY_OPTIONS.index(value) + 1


def save_attitude(db, participant_id, ai_description, fears_rating, fears_text, fears_shared, hopes_rating, hopes_text, hopes_shared, commit=True):
    existing_before = (
        db.query(ParticipantAttitudes)
        .filter(ParticipantAttitudes.participant_id == participant_id, ParticipantAttitudes.phase == "before")
        .order_by(ParticipantAttitudes.attitude_id.desc())
        .first()
    )

    if existing_before:
        existing_before.ai_description = ai_description
        existing_before.fear_rating = fears_rating
        existing_before.fear_text = fears_text
        existing_before.fear_shared_rating = _sharing_index(fears_shared)
        existing_before.hope_rating = hopes_rating
        existing_before.hope_text = hopes_text
        existing_before.hope_shared_rating = _sharing_index(hopes_shared)
        existing_before.created_at = datetime.utcnow()
    else:
        db.add(
            ParticipantAttitudes(
                participant_id=participant_id,
                phase="before",
                ai_description=ai_description,
                fear_rating=fears_rating,
                fear_text=fears_text,
                fear_shared_rating=_sharing_index(fears_shared),
                hope_rating=hopes_rating,
                hope_text=hopes_text,
                hope_shared_rating=_sharing_index(hopes_shared),
                created_at=datetime.utcnow(),
            )
        )

    if commit:
        db.commit()


def save_attitude_after(db, participant_id, fears_rating_after, fears_text_after, fears_shared_after, hopes_rating_after, hopes_text_after, hopes_shared_after, commit=True):
    latest_before = (
        db.query(ParticipantAttitudes)
        .filter(ParticipantAttitudes.participant_id == participant_id, ParticipantAttitudes.phase == "before")
        .order_by(ParticipantAttitudes.attitude_id.desc())
        .first()
    )

    if latest_before:
        latest_before.fear_rating_after = fears_rating_after
        latest_before.fear_text_after = fears_text_after
        latest_before.fear_shared_rating_after = _sharing_index(fears_shared_after)
        latest_before.hope_rating_after = hopes_rating_after
        latest_before.hope_text_after = hopes_text_after
        latest_before.hope_shared_rating_after = _sharing_index(hopes_shared_after)
        latest_before.created_at = datetime.utcnow()
    else:
        db.add(
            ParticipantAttitudes(
                participant_id=participant_id,
                phase="after",
                fear_rating_after=fears_rating_after,
                fear_text_after=fears_text_after,
                fear_shared_rating_after=_sharing_index(fears_shared_after),
                hope_rating_after=hopes_rating_after,
                hope_text_after=hopes_text_after,
                hope_shared_rating_after=_sharing_index(hopes_shared_after),
                created_at=datetime.utcnow(),
            )
        )

    if commit:
        db.commit()


def record_task_event(db, participant_id, task_id, event_type, commit=True):
    db.add(
        ParticipantTaskGalleryEvents(
            participant_id=participant_id,
            task_id=task_id,
            event_type=event_type,
            event_time=datetime.utcnow(),
        )
    )
    if commit:
        db.commit()


def save_ai_behavior(db, participant_id, commit=True, **kwargs):
    behavior = db.query(ParticipantAIBehavior).filter(ParticipantAIBehavior.participant_id == participant_id).first()
    if not behavior:
        behavior = ParticipantAIBehavior(participant_id=participant_id)
        db.add(behavior)

    mapped_values = {
        "ai_familiarity": kwargs.get("ai_familiarity", kwargs.get("smart_devices_recognition")),
        "ai_comfort": kwargs.get("ai_comfort", kwargs.get("ai_skillful_use")),
        "ai_use_frequency": kwargs.get("ai_use_frequency", kwargs.get("ai_application_choice", kwargs.get("ai_work_efficiency"))),
        "ai_trust": kwargs.get("ai_trust", kwargs.get("ai_capabilities_evaluation")),
        "agent_confidence": kwargs.get("agent_confidence", kwargs.get("ai_solution_choice")),
    }

    for field in ["ai_familiarity", "ai_comfort", "ai_use_frequency", "ai_trust", "agent_confidence"]:
        if mapped_values.get(field) is not None:
            setattr(behavior, field, mapped_values[field])

    if commit:
        db.commit()


def save_task_pair_choice(db, participant_id, pair_id, choice_made, commit=True):
    existing = db.query(ParticipantTaskPairChoices).filter(
        ParticipantTaskPairChoices.participant_id == participant_id,
        ParticipantTaskPairChoices.pair_id == pair_id,
    ).first()
    if existing:
        existing.choice_made = choice_made
        existing.created_at = datetime.utcnow()
    else:
        db.add(
            ParticipantTaskPairChoices(
                participant_id=participant_id,
                pair_id=pair_id,
                choice_made=choice_made,
                created_at=datetime.utcnow(),
            )
        )
    if commit:
        db.commit()


def _is_valid_rating(value):
    return isinstance(value, int) and 1 <= value <= 5


def _is_valid_text_response(value):
    normalized_value = (value or "").strip()
    return 70 <= len(normalized_value) <= 350


def validate_final_submission_data():
    errors = []

    prolific_id = (st.session_state.get("prolific_id") or "").strip()
    job_role = (st.session_state.get("job_role") or "").strip()
    if not prolific_id:
        errors.append("Missing required participant identity: prolific_id")
    if not job_role:
        errors.append("Missing required participant identity: job_role")

    profile_data = get_profile_submission_data()
    for field_name in ["age_group", "gender_identity", "ethnicity", "favourite_colour", "education_level"]:
        if not profile_data.get(field_name):
            errors.append(f"Missing required demographics field: {field_name}")

    occupation_fit_choice = get_occupation_fit_submission_data()
    if occupation_fit_choice is None:
        errors.append("Missing required occupation description field")

    ai_description = (st.session_state.get("ai_description") or "").strip()
    if not _is_valid_text_response(ai_description):
        errors.append("Missing or invalid AI description")

    before_payload = get_before_attitude_submission_data()
    after_payload = get_after_attitude_submission_data()

    if not _is_valid_rating(before_payload["fears_rating"]):
        errors.append("Missing or invalid before fear rating")
    if not _is_valid_text_response(before_payload["fears_text"]):
        errors.append("Missing or invalid before fear text")
    if before_payload["fears_shared"] not in SHARED_FREQUENCY_OPTIONS:
        errors.append("Missing or invalid before fear shared rating")
    if not _is_valid_rating(before_payload["hopes_rating"]):
        errors.append("Missing or invalid before hope rating")
    if not _is_valid_text_response(before_payload["hopes_text"]):
        errors.append("Missing or invalid before hope text")
    if before_payload["hopes_shared"] not in SHARED_FREQUENCY_OPTIONS:
        errors.append("Missing or invalid before hope shared rating")

    if not _is_valid_rating(after_payload["fears_rating_after"]):
        errors.append("Missing or invalid after fear rating")
    if not _is_valid_text_response(after_payload["fears_text_after"]):
        errors.append("Missing or invalid after fear text")
    if after_payload["fears_shared_after"] not in SHARED_FREQUENCY_OPTIONS:
        errors.append("Missing or invalid after fear shared rating")
    if not _is_valid_rating(after_payload["hopes_rating_after"]):
        errors.append("Missing or invalid after hope rating")
    if not _is_valid_text_response(after_payload["hopes_text_after"]):
        errors.append("Missing or invalid after hope text")
    if after_payload["hopes_shared_after"] not in SHARED_FREQUENCY_OPTIONS:
        errors.append("Missing or invalid after hope shared rating")

    likert_payload = {key: st.session_state.get(key) for key in PAGE6_LIKERT_KEYS}
    invalid_likert_keys = [key for key, value in likert_payload.items() if value not in LIKERT_SCALE_OPTIONS]
    for key in invalid_likert_keys:
        errors.append(f"Missing or invalid AI experience field: {key}")

    expected_pair_ids = [pair["pair_id"] for pair in get_task_pairs_for_ui() if pair["pair_id"] > 0]
    pair_choices = st.session_state.get("pair_choices", {})
    missing_pair_ids = [pair_id for pair_id in expected_pair_ids if pair_choices.get(pair_id) not in {"left", "right", "skip"}]
    if missing_pair_ids:
        errors.append("Missing one or more task pair choices")

    return {
        "errors": errors,
        "prolific_id": prolific_id,
        "job_role": job_role,
        "profile_data": profile_data,
        "occupation_fit_choice": occupation_fit_choice,
        "ai_description": ai_description,
        "before_payload": before_payload,
        "after_payload": after_payload,
        "likert_payload": likert_payload,
        "pair_choices": pair_choices,
        "pending_task_events": st.session_state.get("pending_task_events", []),
    }


@st.cache_data(show_spinner=False, ttl=30)
def load_task_pairs():
    db = SessionLocal()
    try:
        pairs = db.query(TaskPairs).filter(TaskPairs.is_active == True).order_by(TaskPairs.pair_order).all()
        result = []
        for pair in pairs:
            left = db.query(OccupationTask.task_id, OccupationTask.task_name, OccupationTask.task_description).filter(
                OccupationTask.task_id == pair.left_task_id
            ).first()
            right = db.query(OccupationTask.task_id, OccupationTask.task_name, OccupationTask.task_description).filter(
                OccupationTask.task_id == pair.right_task_id
            ).first()
            if left and right:
                result.append(
                    {
                        "pair_id": pair.pair_id,
                        "left": {"task_id": left.task_id, "title": left.task_name, "description": left.task_description or ""},
                        "right": {"task_id": right.task_id, "title": right.task_name, "description": right.task_description or ""},
                    }
                )
        return result
    except Exception:
        return []
    finally:
        db.close()


@st.cache_data(show_spinner=False, ttl=30)
def load_tasks(occupation_name=None):
    db = SessionLocal()
    try:
        color_to_risk = {"red": "HIGH", "yellow": "MEDIUM", "green": "LOW"}
        query = db.query(
            OccupationTask.task_id,
            OccupationTask.task_name,
            OccupationTask.task_description,
            OccupationTask.justification,
            OccupationTask.exposure_label,
            OccupationTask.mp_label,
            OccupationTask.td_label,
            OccupationTask.vr_label,
            OccupationTask.eh_label,
            OccupationTask.color_code,
            OccupationTask.is_active,
        ).filter(OccupationTask.is_active == True)

        if occupation_name:
            occ = db.query(Occupation.occupation_id).filter(Occupation.occupation_name == occupation_name).first()
            if occ:
                query = query.filter(OccupationTask.occupation_id == occ.occupation_id)

        tasks = query.order_by(OccupationTask.task_order.asc(), OccupationTask.task_id.asc()).all()
        return [
            {
                "id": task.task_id,
                "title": task.task_name,
                "risk_level": color_to_risk.get((task.color_code or "").lower(), "MEDIUM"),
                "automation_level": "MEDIUM",
                "description": task.task_description or "",
                "capability": (task.task_description or "").strip() or "No AI Agent capability description provided for this task.",
                "example_tech": ", ".join(
                    [
                        value.strip()
                        for value in [task.exposure_label, task.mp_label, task.td_label, task.vr_label, task.eh_label]
                        if isinstance(value, str) and value.strip()
                    ]
                ) or "No example technology information provided for this task.",
                "dimensions": ["Mental", "Routine"],
                "risk_analysis": (task.justification or "").strip() or "No risk analysis provided for this task.",
            }
            for task in tasks
        ]
    except Exception:
        return []
    finally:
        db.close()


@st.cache_data(show_spinner=False, ttl=30)
def load_job_roles():
    db = SessionLocal()
    try:
        rows = db.query(Occupation.occupation_name).filter(Occupation.is_active == True).order_by(Occupation.occupation_name.asc()).all()
        return [row.occupation_name for row in rows if row.occupation_name]
    except Exception:
        return []
    finally:
        db.close()


@st.cache_data(show_spinner=False, ttl=5)
def get_runtime_db_status():
    status = {"connected": False, "database": "unknown", "error": ""}
    if DB_CONFIG_ERROR:
        status["error"] = DB_CONFIG_ERROR
        return status
    if DB_INIT_ERROR is not None:
        status["error"] = DB_INIT_ERROR
        return status
    try:
        with engine.connect() as conn:
            status["connected"] = True
            db_name = conn.execute(text("SELECT DATABASE()")).scalar()
            status["database"] = db_name or "unknown"
    except Exception as exc:
        status["error"] = str(exc).splitlines()[0]
    return status


def get_runtime_db_display_text(status):
    if status["connected"]:
        return f"CONNECTED ({status['database']})"
    return "DISCONNECTED"


def render_runtime_status_banner(page_number):
    db_tasks = load_tasks(st.session_state.get("job_role")) if page_number >= 4 else []
    db_pairs_preview = load_task_pairs() if page_number >= 7 else []
    runtime_db = get_runtime_db_status() if page_number >= 1 else {"connected": False, "database": "unknown", "error": ""}
    task_gallery_source = "DB" if db_tasks else "MOCK"
    task_pairs_source = "DB" if db_pairs_preview else "MOCK"
    db_state_text = get_runtime_db_display_text(runtime_db)
    db_state_bg = "#ecfdf5" if runtime_db["connected"] else "#fef2f2"
    db_state_border = "#16a34a" if runtime_db["connected"] else "#dc2626"
    st.markdown(
        f"""
        <div style='margin: 6px 0 14px 0; padding: 10px 12px; border-radius: 8px;
                    border: 1px solid {db_state_border}; background: {db_state_bg}; font-size: 13px;'>
            <strong>Runtime Data Source</strong><br>
            DB: {db_state_text} | Task Gallery: {task_gallery_source} | Task Pairs: {task_pairs_source}
        </div>
        """,
        unsafe_allow_html=True,
    )


def queue_task_event(task_id, event_type):
    if "pending_task_events" not in st.session_state:
        st.session_state.pending_task_events = []
    st.session_state.pending_task_events.append({"task_id": task_id, "event_type": event_type})


def get_job_roles_for_ui():
    db_job_roles = load_job_roles() if st.session_state.page >= 1 else []
    return db_job_roles if db_job_roles else DEFAULT_JOB_ROLES


def get_tasks_gallery_for_ui():
    db_tasks = load_tasks(st.session_state.get("job_role")) if st.session_state.page >= 4 else []
    return db_tasks if db_tasks else MOCK_TASKS


def get_task_pairs_for_ui():
    db_pairs = load_task_pairs() if st.session_state.page >= 7 else []
    return db_pairs if db_pairs else MOCK_PAIRS


def finalize_submission_to_db():
    submission_data = validate_final_submission_data()
    if submission_data["errors"]:
        raise ValueError(submission_data["errors"][0])

    likert_values = {opt: i + 1 for i, opt in enumerate(LIKERT_SCALE_OPTIONS)}

    db = SessionLocal()
    try:
        participant_id = resolve_participant_id_for_submission(
            db,
            submission_data["prolific_id"],
            submission_data["job_role"],
            occupation_id=st.session_state.get("selected_occupation_id"),
        )
        st.session_state.participant_id = participant_id

        save_profile(
            db,
            participant_id,
            commit=False,
            age_group=submission_data["profile_data"]["age_group"],
            gender_identity=submission_data["profile_data"]["gender_identity"],
            ethnicity=submission_data["profile_data"]["ethnicity"],
            favourite_colour=submission_data["profile_data"]["favourite_colour"],
            education_level=submission_data["profile_data"]["education_level"],
            occupation_description=submission_data["occupation_fit_choice"],
        )

        save_attitude(
            db,
            participant_id,
            submission_data["ai_description"],
            submission_data["before_payload"]["fears_rating"],
            submission_data["before_payload"]["fears_text"],
            submission_data["before_payload"]["fears_shared"],
            submission_data["before_payload"]["hopes_rating"],
            submission_data["before_payload"]["hopes_text"],
            submission_data["before_payload"]["hopes_shared"],
            commit=False,
        )

        save_ai_behavior(
            db,
            participant_id,
            commit=False,
            occupation_fit=OCCUPATION_FIT_OPTIONS.index(submission_data["occupation_fit_choice"]),
            smart_devices_recognition=likert_values[submission_data["likert_payload"]["smart_devices"]],
            ai_help_uncertainty=likert_values[submission_data["likert_payload"]["ai_help"]],
            ai_technology_identification=likert_values[submission_data["likert_payload"]["ai_tech_id"]],
            ai_skillful_use=likert_values[submission_data["likert_payload"]["ai_skillful"]],
            ai_learning_difficulty=likert_values[submission_data["likert_payload"]["ai_learning"]],
            ai_work_efficiency=likert_values[submission_data["likert_payload"]["ai_efficiency"]],
            ai_capabilities_evaluation=likert_values[submission_data["likert_payload"]["ai_eval"]],
            ai_solution_choice=likert_values[submission_data["likert_payload"]["ai_solution"]],
            attention_check=likert_values[submission_data["likert_payload"]["attention_check"]],
            ai_application_choice=likert_values[submission_data["likert_payload"]["ai_choice"]],
            ethical_compliance=likert_values[submission_data["likert_payload"]["ethical"]],
            privacy_alertness=likert_values[submission_data["likert_payload"]["privacy"]],
            ai_abuse_alertness=likert_values[submission_data["likert_payload"]["ai_abuse"]],
        )

        for pair_id, choice in submission_data["pair_choices"].items():
            if pair_id > 0:
                save_task_pair_choice(db, participant_id, pair_id, choice, commit=False)

        for event in submission_data["pending_task_events"]:
            record_task_event(db, participant_id, event["task_id"], event["event_type"], commit=False)

        save_attitude_after(
            db,
            participant_id,
            submission_data["after_payload"]["fears_rating_after"],
            submission_data["after_payload"]["fears_text_after"],
            submission_data["after_payload"]["fears_shared_after"],
            submission_data["after_payload"]["hopes_rating_after"],
            submission_data["after_payload"]["hopes_text_after"],
            submission_data["after_payload"]["hopes_shared_after"],
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()