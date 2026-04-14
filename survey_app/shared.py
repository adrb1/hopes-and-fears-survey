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
    "Data Analyst",
    "Teacher/Educator",
    "Healthcare Professional",
    "Business Manager",
    "Marketing Professional",
    "Customer Service Representative",
    "Content Writer",
    "Graphic Designer",
    "Project Manager",
]

SHARED_FREQUENCY_OPTIONS = [
    "",
    "Not at all",
    "Rarely",
    "Occasionally",
    "Moderately",
    "Often",
    "Very often",
    "Almost always",
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

OCCUPATION_FIT_OPTIONS = [
    "My occupation requires minimal prior experience or training, potentially needs a high school diploma or GED, and typically involves a brief training period of a few days to a few months.",
    "My occupation requires a high school diploma, several months to a year of training, and often involve assisting others.",
    "My occupation requires vocational training, a college degree, or specialized certifications, and typically involves complex problem-solving, creativity, or advanced technical skills.",
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
        "example_tech": "AI-powered CRM systems like Salesforce Einstein or HubSpot AI can automatically process, categorize, and respond to routine correspondence.",
        "dimensions": ["Mental", "Individual", "Routine", "Easy"],
        "risk_analysis": "High risk due to potential errors in automated correspondence that could damage professional relationships. AI may misinterpret context or tone, leading to inappropriate responses. Requires careful monitoring and human oversight for complex communications.",
    },
    {
        "id": 2,
        "title": "Generate lesson plans",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Generate lesson plans tailored to different student levels and educational needs.",
        "capability": "AI can analyze curriculum standards and student data to create customized, adaptive lesson plans that cater to diverse learning styles and pace.",
        "example_tech": "AI tools like ChatGPT, Google's NotebookLM, and specialized education platforms can generate structured lesson plans in minutes.",
        "dimensions": ["Mental", "Individual", "Routine", "Easy"],
        "risk_analysis": "Low risk as AI-generated lesson plans can be reviewed and customized by teachers. The technology enhances efficiency while maintaining educational quality and teacher expertise.",
    },
    {
        "id": 3,
        "title": "Schedule meetings",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Schedule and coordinate meetings across teams and time zones.",
        "capability": "AI can analyze calendars, preferences, and time zones to find optimal meeting times and send invitations automatically.",
        "example_tech": "Tools like Microsoft Copilot for Outlook and scheduling assistants can automate meeting coordination.",
        "dimensions": ["Mental", "Routine", "Easy"],
        "risk_analysis": "Medium risk as scheduling conflicts or misinterpretations of availability could occur. However, most scheduling issues are recoverable and AI can significantly reduce coordination overhead.",
    },
    {
        "id": 4,
        "title": "Analyze student performance",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Analyze student performance data and generate insights.",
        "capability": "AI can process large datasets, identify patterns, and generate actionable insights on student learning trends and areas needing support.",
        "example_tech": "Learning analytics platforms powered by AI can track progress and recommend interventions.",
        "dimensions": ["Mental", "Individual", "Easy"],
        "risk_analysis": "Low risk as AI analytics provide data-driven insights that complement teacher judgment. Teachers retain final decision-making authority while benefiting from comprehensive data analysis.",
    },
    {
        "id": 5,
        "title": "Write emails",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Compose and send routine emails.",
        "capability": "AI can draft professional emails based on templates and context, significantly reducing composition time.",
        "example_tech": "AI writing assistants like Grammarly AI and email plugins can auto-generate email content.",
        "dimensions": ["Mental", "Routine", "Easy"],
        "risk_analysis": "Medium risk due to potential miscommunication from AI-generated content. Tone, context, and nuanced language may not be perfectly captured, requiring human review for important communications.",
    },
    {
        "id": 6,
        "title": "Create content",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Create educational content, summaries, and explanations.",
        "capability": "AI can generate diverse content formats from text to multimedia, adapting to different learning preferences.",
        "example_tech": "Generative AI models like GPT-4 and specialized content creation tools can produce educational materials.",
        "dimensions": ["Mental", "Individual"],
        "risk_analysis": "Medium risk as AI-generated content may lack depth or contain inaccuracies. Educational content requires accuracy and pedagogical expertise, so human review and customization are essential.",
    },
    {
        "id": 7,
        "title": "Grade assignments",
        "risk_level": "HIGH",
        "automation_level": "MEDIUM",
        "description": "Grade assignments and provide feedback.",
        "capability": "AI can evaluate objective assessments and provide personalized feedback, though subjective work still benefits from human review.",
        "example_tech": "AI-powered grading systems can score tests and essays with human-in-the-loop review.",
        "dimensions": ["Routine", "Easy"],
        "risk_analysis": "High risk due to the subjective nature of assessment and potential bias in AI grading algorithms. Student grades significantly impact educational and career opportunities, requiring human judgment.",
    },
    {
        "id": 8,
        "title": "Monitor student progress",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Monitor student progress and flag concerns.",
        "capability": "Continuous AI monitoring can track learning metrics and alert educators to struggling students in real-time.",
        "example_tech": "Learning management systems with AI analytics provide real-time student progress monitoring.",
        "dimensions": ["Mental", "Routine"],
        "risk_analysis": "Low risk as AI monitoring serves as an early warning system that enhances teacher effectiveness. Teachers can intervene based on AI alerts while maintaining oversight of student development.",
    },
    {
        "id": 9,
        "title": "Content moderation",
        "risk_level": "HIGH",
        "automation_level": "HIGH",
        "description": "Moderate user-generated content and discussions.",
        "capability": "AI can identify inappropriate content, spam, and policy violations across large volumes of text and media.",
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
        "capability": "AI tutors can adapt to individual learning speeds, answer questions 24/7, and provide unlimited practice with feedback.",
        "example_tech": "AI tutoring platforms like Carnegie Learning and Squirrel AI offer adaptive learning experiences.",
        "dimensions": ["Mental", "Individual"],
        "risk_analysis": "Low risk as AI tutoring supplements rather than replaces human instruction. Students benefit from 24/7 access to practice and immediate feedback while teachers focus on complex learning needs.",
    },
    {
        "id": 11,
        "title": "Data entry",
        "risk_level": "LOW",
        "automation_level": "HIGH",
        "description": "Enter data into systems and databases.",
        "capability": "AI can extract, validate, and enter data with high accuracy, reducing manual data entry errors.",
        "example_tech": "RPA tools and AI OCR systems automate data entry from various sources.",
        "dimensions": ["Routine", "Easy"],
        "risk_analysis": "Low risk as data entry is highly automatable with minimal consequences for errors. AI can achieve higher accuracy than manual entry while freeing humans for more valuable tasks.",
    },
    {
        "id": 12,
        "title": "Curriculum design",
        "risk_level": "MEDIUM",
        "automation_level": "MEDIUM",
        "description": "Design and develop new curricula.",
        "capability": "AI can assist in curriculum development by analyzing standards, suggesting best practices, and ensuring alignment.",
        "example_tech": "AI curriculum tools can help map learning objectives and suggest content sequences.",
        "dimensions": ["Mental", "Individual"],
        "risk_analysis": "Medium risk as curriculum design requires deep pedagogical knowledge and cultural context. AI can assist but cannot replace the expertise needed for comprehensive educational program development.",
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
    {
        "pair_id": -4,
        "left": {"task_id": 6, "title": "Create content", "description": "Create educational content, summaries, and explanations."},
        "right": {"task_id": 8, "title": "Monitor student progress", "description": "Monitor student progress and flag concerns."},
    },
    {
        "pair_id": -5,
        "left": {"task_id": 10, "title": "Personalized tutoring", "description": "Provide personalized tutoring and one-on-one support."},
        "right": {"task_id": 9, "title": "Content moderation", "description": "Moderate user-generated content and discussions."},
    },
    {
        "pair_id": -6,
        "left": {"task_id": 11, "title": "Data entry", "description": "Enter data into systems and databases."},
        "right": {"task_id": 12, "title": "Curriculum design", "description": "Design and develop new curricula."},
    },
]

SESSION_DEFAULTS = {
    "page": 0,
    "participant_id": None,
    "prolific_id": "",
    "job_role": "",
    "job_role_other": "",
    "ai_description": "",
    "fears_rating": 3,
    "hopes_rating": 3,
    "fears_text": "",
    "hopes_text": "",
    "fears_shared": None,
    "hopes_shared": None,
    "selected_task": None,
    "page6_question_index": 0,
    "pair_index": 0,
    "pair_choices": {},
    "fears_rating_after": 3,
    "hopes_rating_after": 3,
    "fears_text_after": "",
    "hopes_text_after": "",
    "fears_shared_after": None,
    "hopes_shared_after": None,
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
    "occupation_fit_radio": "",
    "smart_devices": "",
    "ai_help": "",
    "ai_tech_id": "",
    "ai_skillful": "",
    "ai_learning": "",
    "ai_efficiency": "",
    "ai_eval": "",
    "ai_solution": "",
    "attention_check": "",
    "ai_choice": "",
    "ethical": "",
    "privacy": "",
    "ai_abuse": "",
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
            "Under 18",
            "18-24 years old",
            "25-34 years old",
            "35-44 years old",
            "45-54 years old",
            "55-64 years old",
            "65+ years old",
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


@st.cache_resource(show_spinner=False)
def initialize_database_schema():
    Base.metadata.create_all(bind=engine)
    ensure_participant_attitudes_after_columns()


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
        db.commit()
        db.refresh(occ)
    return occ


def get_or_create_participant(db, prolific_id, occupation_name):
    participant = db.query(Participant).filter(Participant.prolific_id == prolific_id).first()
    occ = get_or_create_occupation(db, occupation_name)
    if not participant:
        participant = Participant(prolific_id=prolific_id, occupation_id=occ.occupation_id, entry_date=datetime.utcnow())
        db.add(participant)
        db.commit()
        db.refresh(participant)
    else:
        participant.occupation_id = occ.occupation_id
        db.commit()
    return participant.participant_id


def save_profile(db, participant_id, **kwargs):
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

    db.commit()


def _sharing_index(value):
    return SHARED_FREQUENCY_OPTIONS[1:].index(value) + 1


def save_attitude(db, participant_id, ai_description, fears_rating, fears_text, fears_shared, hopes_rating, hopes_text, hopes_shared):
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

    db.commit()


def save_attitude_after(db, participant_id, fears_rating_after, fears_text_after, fears_shared_after, hopes_rating_after, hopes_text_after, hopes_shared_after):
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

    db.commit()


def record_task_event(db, participant_id, task_id, event_type):
    db.add(
        ParticipantTaskGalleryEvents(
            participant_id=participant_id,
            task_id=task_id,
            event_type=event_type,
            event_time=datetime.utcnow(),
        )
    )
    db.commit()


def save_ai_behavior(db, participant_id, **kwargs):
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

    db.commit()


def save_task_pair_choice(db, participant_id, pair_id, choice_made):
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
    db.commit()


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
                "capability": (task.task_description or "").strip() or "No AI capability description provided for this task.",
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
    prolific_id = (st.session_state.get("prolific_id") or "").strip()
    job_role = st.session_state.get("job_role") or ""
    if not prolific_id or not job_role:
        raise ValueError("Missing required participant identity fields")

    final_gender = st.session_state.get("gender_other", "").strip() if st.session_state.get("gender_identity") == "Other" else st.session_state.get("gender_identity")
    final_ethnicity = st.session_state.get("ethnicity_other", "").strip() if st.session_state.get("ethnicity") == "Other" else st.session_state.get("ethnicity")
    final_education = st.session_state.get("education_other", "").strip() if st.session_state.get("education_level") == "Other" else st.session_state.get("education_level")

    occupation_fit_choice = st.session_state.get("occupation_fit_radio", OCCUPATION_FIT_OPTIONS[0])
    if occupation_fit_choice not in OCCUPATION_FIT_OPTIONS:
        occupation_fit_choice = OCCUPATION_FIT_OPTIONS[0]

    likert_values = {opt: i for i, opt in enumerate(LIKERT_SCALE_OPTIONS)}

    db = SessionLocal()
    try:
        participant_id = get_or_create_participant(db, prolific_id, job_role)
        st.session_state.participant_id = participant_id

        save_profile(
            db,
            participant_id,
            age_group=st.session_state.get("age_group"),
            gender_identity=final_gender,
            ethnicity=final_ethnicity,
            favourite_colour=st.session_state.get("favourite_colour"),
            education_level=final_education,
            occupation_description=occupation_fit_choice,
        )

        save_attitude(
            db,
            participant_id,
            st.session_state.get("ai_description"),
            st.session_state.get("fears_rating"),
            st.session_state.get("fears_text"),
            st.session_state.get("fears_shared"),
            st.session_state.get("hopes_rating"),
            st.session_state.get("hopes_text"),
            st.session_state.get("hopes_shared"),
        )

        save_ai_behavior(
            db,
            participant_id,
            occupation_fit=OCCUPATION_FIT_OPTIONS.index(occupation_fit_choice),
            smart_devices_recognition=likert_values[st.session_state.get("smart_devices")],
            ai_help_uncertainty=likert_values[st.session_state.get("ai_help")],
            ai_technology_identification=likert_values[st.session_state.get("ai_tech_id")],
            ai_skillful_use=likert_values[st.session_state.get("ai_skillful")],
            ai_learning_difficulty=likert_values[st.session_state.get("ai_learning")],
            ai_work_efficiency=likert_values[st.session_state.get("ai_efficiency")],
            ai_capabilities_evaluation=likert_values[st.session_state.get("ai_eval")],
            ai_solution_choice=likert_values[st.session_state.get("ai_solution")],
            attention_check=likert_values[st.session_state.get("attention_check")],
            ai_application_choice=likert_values[st.session_state.get("ai_choice")],
            ethical_compliance=likert_values[st.session_state.get("ethical")],
            privacy_alertness=likert_values[st.session_state.get("privacy")],
            ai_abuse_alertness=likert_values[st.session_state.get("ai_abuse")],
        )

        for pair_id, choice in st.session_state.get("pair_choices", {}).items():
            if pair_id > 0:
                save_task_pair_choice(db, participant_id, pair_id, choice)

        for event in st.session_state.get("pending_task_events", []):
            record_task_event(db, participant_id, event["task_id"], event["event_type"])

        save_attitude_after(
            db,
            participant_id,
            st.session_state.get("fears_rating_after"),
            st.session_state.get("fears_text_after"),
            st.session_state.get("fears_shared_after"),
            st.session_state.get("hopes_rating_after"),
            st.session_state.get("hopes_text_after"),
            st.session_state.get("hopes_shared_after"),
        )
    finally:
        db.close()