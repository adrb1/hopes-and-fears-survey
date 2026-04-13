import os
import threading
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import create_engine, Column, Integer, BigInteger, SmallInteger, String, Text, Boolean, DateTime, ForeignKey, Enum, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Page configuration
st.set_page_config(page_title="Hopes & Fears Survey", layout="centered")

# Restrict main container width for non-fullscreen layout
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
        .css-1d391kg, .css-1bn9ls4 {
            max-width: 960px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Block copy/paste in all text fields to reduce response duplication from external sources.
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

                    // Copy/cut are always blocked (including Prolific ID).
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

                doc.addEventListener(
                    "keydown",
                    (e) => {
                        const field = isTextField(e.target)
                            ? e.target
                            : (isTextField(doc.activeElement) ? doc.activeElement : null);
                        if (!field) return;
                        const key = (e.key || "").toLowerCase();
                        const combo = e.ctrlKey || e.metaKey;
                        const prolificPaste =
                            isProlificField(field) &&
                            ((combo && key === "v") || (e.shiftKey && key === "insert"));
                        if (prolificPaste) return;
                        if ((combo && ["c", "v", "x", "insert"].includes(key)) || (e.shiftKey && key === "insert")) {
                            e.preventDefault();
                            e.stopPropagation();
                        }
                    },
                    true
                );
            })();
        </script>
        """,
        height=0,
)

# Database config
# Priority order:
# 1. SSH tunnel secrets (ssh_* + db_*)
# 2. Streamlit secrets/environment DB URL
# 3. Local fallback SQLite for development/demo use
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

    # Start tunnel with a timeout so the app never hangs indefinitely
    _error: list = [None]

    def _start():
        try:
            tunnel.start()
        except Exception as exc:
            _error[0] = exc

    _t = threading.Thread(target=_start, daemon=True)
    _t.start()
    _t.join(timeout=6)
    if _t.is_alive():
        raise TimeoutError("SSH tunnel did not connect within 6 seconds")
    if _error[0] is not None:
        raise _error[0]

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

# ORM models 
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
        "primary_key": [
            employment_role,
            task_name,
            exposure,
            mp,
            td,
            vr,
            eh,
            justification,
        ]
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

try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    DB_INIT_ERROR = str(exc).splitlines()[0]


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


ensure_participant_attitudes_after_columns()

# Helpers
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
        db.query(ParticipantProfile).filter(
            ParticipantProfile.participant_id == participant_id
        ).update(update_values, synchronize_session=False)

    db.commit()


def save_attitude(db, participant_id, ai_description, fears_rating, fears_text, fears_shared, hopes_rating, hopes_text, hopes_shared):
    sharing_index = lambda v: ["Not at all", "Rarely", "Occasionally", "Moderately", "Often", "Very often", "Almost always"].index(v) + 1
    existing_before = (
        db.query(ParticipantAttitudes)
        .filter(
            ParticipantAttitudes.participant_id == participant_id,
            ParticipantAttitudes.phase == "before",
        )
        .order_by(ParticipantAttitudes.attitude_id.desc())
        .first()
    )

    if existing_before:
        existing_before.ai_description = ai_description
        existing_before.fear_rating = fears_rating
        existing_before.fear_text = fears_text
        existing_before.fear_shared_rating = sharing_index(fears_shared)
        existing_before.hope_rating = hopes_rating
        existing_before.hope_text = hopes_text
        existing_before.hope_shared_rating = sharing_index(hopes_shared)
        existing_before.created_at = datetime.utcnow()
    else:
        att = ParticipantAttitudes(
            participant_id=participant_id,
            phase="before",
            ai_description=ai_description,
            fear_rating=fears_rating,
            fear_text=fears_text,
            fear_shared_rating=sharing_index(fears_shared),
            hope_rating=hopes_rating,
            hope_text=hopes_text,
            hope_shared_rating=sharing_index(hopes_shared),
            created_at=datetime.utcnow()
        )
        db.add(att)

    db.commit()

def save_attitude_after(db, participant_id, fears_rating_after, fears_text_after, fears_shared_after, hopes_rating_after, hopes_text_after, hopes_shared_after):
    sharing_index = lambda v: ["Not at all", "Rarely", "Occasionally", "Moderately", "Often", "Very often", "Almost always"].index(v) + 1
    latest_before = (
        db.query(ParticipantAttitudes)
        .filter(
            ParticipantAttitudes.participant_id == participant_id,
            ParticipantAttitudes.phase == "before",
        )
        .order_by(ParticipantAttitudes.attitude_id.desc())
        .first()
    )

    if latest_before:
        latest_before.fear_rating_after = fears_rating_after
        latest_before.fear_text_after = fears_text_after
        latest_before.fear_shared_rating_after = sharing_index(fears_shared_after)
        latest_before.hope_rating_after = hopes_rating_after
        latest_before.hope_text_after = hopes_text_after
        latest_before.hope_shared_rating_after = sharing_index(hopes_shared_after)
        latest_before.created_at = datetime.utcnow()
    else:
        db.add(
            ParticipantAttitudes(
                participant_id=participant_id,
                phase="after",
                fear_rating_after=fears_rating_after,
                fear_text_after=fears_text_after,
                fear_shared_rating_after=sharing_index(fears_shared_after),
                hope_rating_after=hopes_rating_after,
                hope_text_after=hopes_text_after,
                hope_shared_rating_after=sharing_index(hopes_shared_after),
                created_at=datetime.utcnow(),
            )
        )

    db.commit()

def record_task_event(db, participant_id, task_id, event_type):
    ev = ParticipantTaskGalleryEvents(
        participant_id=participant_id,
        task_id=task_id,
        event_type=event_type,
        event_time=datetime.utcnow()
    )
    db.add(ev)
    db.commit()

def save_ai_behavior(db, participant_id, **kwargs):
    behavior = db.query(ParticipantAIBehavior).filter(ParticipantAIBehavior.participant_id == participant_id).first()
    if not behavior:
        behavior = ParticipantAIBehavior(participant_id=participant_id)
        db.add(behavior)

    # Backward-compatible mapping from current survey keys to participant_ai_scale columns.
    mapped_values = {
        "ai_familiarity": kwargs.get("ai_familiarity", kwargs.get("smart_devices_recognition")),
        "ai_comfort": kwargs.get("ai_comfort", kwargs.get("ai_skillful_use")),
        "ai_use_frequency": kwargs.get("ai_use_frequency", kwargs.get("ai_application_choice", kwargs.get("ai_work_efficiency"))),
        "ai_trust": kwargs.get("ai_trust", kwargs.get("ai_capabilities_evaluation")),
        "agent_confidence": kwargs.get("agent_confidence", kwargs.get("ai_solution_choice")),
    }

    fields = ["ai_familiarity", "ai_comfort", "ai_use_frequency", "ai_trust", "agent_confidence"]
    for field in fields:
        if mapped_values.get(field) is not None:
            setattr(behavior, field, mapped_values[field])

    db.commit()

def save_task_pair_choice(db, participant_id, pair_id, choice_made):
    existing = db.query(ParticipantTaskPairChoices).filter(
        ParticipantTaskPairChoices.participant_id == participant_id,
        ParticipantTaskPairChoices.pair_id == pair_id
    ).first()
    if existing:
        existing.choice_made = choice_made
        existing.created_at = datetime.utcnow()
    else:
        choice = ParticipantTaskPairChoices(
            participant_id=participant_id,
            pair_id=pair_id,
            choice_made=choice_made,
            created_at=datetime.utcnow()
        )
        db.add(choice)
    db.commit()

@st.cache_data(show_spinner=False)
@st.cache_data(show_spinner=False, ttl=30)
def load_task_pairs():
    db = SessionLocal()
    try:
        pairs = db.query(TaskPairs).filter(TaskPairs.is_active == True).order_by(TaskPairs.pair_order).all()
        result = []
        for p in pairs:
            left = db.query(
                OccupationTask.task_id,
                OccupationTask.task_name,
                OccupationTask.task_description,
            ).filter(OccupationTask.task_id == p.left_task_id).first()
            right = db.query(
                OccupationTask.task_id,
                OccupationTask.task_name,
                OccupationTask.task_description,
            ).filter(OccupationTask.task_id == p.right_task_id).first()
            if left and right:
                result.append({
                    "pair_id": p.pair_id,
                    "left": {"task_id": left.task_id, "title": left.task_name, "description": left.task_description or ""},
                    "right": {"task_id": right.task_id, "title": right.task_name, "description": right.task_description or ""}
                })
        return result
    except Exception:
        return []
    finally:
        db.close()

@st.cache_data(show_spinner=False)
@st.cache_data(show_spinner=False, ttl=30)
def load_tasks(occupation_name=None):
    db = SessionLocal()
    try:
        color_to_risk = {
            "red": "HIGH",
            "yellow": "MEDIUM",
            "green": "LOW",
        }
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
            occ = (
                db.query(Occupation.occupation_id)
                .filter(Occupation.occupation_name == occupation_name)
                .first()
            )
            if occ:
                query = query.filter(OccupationTask.occupation_id == occ.occupation_id)

        tasks = query.order_by(OccupationTask.task_order.asc(), OccupationTask.task_id.asc()).all()
        return [
            {
                "id": t.task_id,
                "title": t.task_name,
                "risk_level": color_to_risk.get((t.color_code or "").lower(), "MEDIUM"),
                "automation_level": "MEDIUM",
                "description": t.task_description or "",
                "capability": (t.task_description or "").strip() or "No AI capability description provided for this task.",
                "example_tech": ", ".join(
                    [
                        v.strip()
                        for v in [t.exposure_label, t.mp_label, t.td_label, t.vr_label, t.eh_label]
                        if isinstance(v, str) and v.strip()
                    ]
                ) or "No example technology information provided for this task.",
                "dimensions": ["Mental", "Routine"],
                "risk_analysis": (t.justification or "").strip() or "No risk analysis provided for this task."
            }
            for t in tasks
        ]
    except Exception:
        return []
    finally:
        db.close()


@st.cache_data(show_spinner=False, ttl=30)
def load_job_roles():
    db = SessionLocal()
    try:
        rows = (
            db.query(Occupation.occupation_name)
            .filter(Occupation.is_active == True)
            .order_by(Occupation.occupation_name.asc())
            .all()
        )
        return [r.occupation_name for r in rows if r.occupation_name]
    except Exception:
        return []
    finally:
        db.close()


@st.cache_data(show_spinner=False, ttl=5)
def get_runtime_db_status():
    status = {
        "connected": False,
        "database": "unknown",
        "error": "",
    }
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

# Initialization for session data
if "page" not in st.session_state:
    st.session_state.page = 0
if "participant_id" not in st.session_state:
    st.session_state.participant_id = None


# Custom CSS for consistent slider styling
st.markdown("""
<style>
/* Consistent font for all sliders */
[data-testid="stSlider"] .stSlider {
    all_consented = consent_read and consent_age and consent_participate
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
}
        if st.button("Proceed to survey →", key="consent_next", disabled=not all_consented):
            if all_consented:
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
}

/* Ensure consistent spacing */
.stSlider, .stSelectSlider {
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = 0
if "prolific_id" not in st.session_state:
    st.session_state.prolific_id = ""
if "job_role" not in st.session_state:
    st.session_state.job_role = ""
if "job_role_other" not in st.session_state:
    st.session_state.job_role_other = ""
if "ai_description" not in st.session_state:
    st.session_state.ai_description = ""
if "fears_rating" not in st.session_state:
    st.session_state.fears_rating = 3
if "hopes_rating" not in st.session_state:
    st.session_state.hopes_rating = 3
if "fears_text" not in st.session_state:
    st.session_state.fears_text = ""
if "hopes_text" not in st.session_state:
    st.session_state.hopes_text = ""
if "fears_shared" not in st.session_state:
    st.session_state.fears_shared = None
if "hopes_shared" not in st.session_state:
    st.session_state.hopes_shared = None
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None
if "page6_question_index" not in st.session_state:
    st.session_state.page6_question_index = 0
if "pair_index" not in st.session_state:
    st.session_state.pair_index = 0
if "pair_choices" not in st.session_state:
    st.session_state.pair_choices = {}  # {pair_id: 'left'|'right'|'skip'}
if "fears_rating_after" not in st.session_state:
    st.session_state.fears_rating_after = 3
if "hopes_rating_after" not in st.session_state:
    st.session_state.hopes_rating_after = 3
if "fears_text_after" not in st.session_state:
    st.session_state.fears_text_after = ""
if "hopes_text_after" not in st.session_state:
    st.session_state.hopes_text_after = ""
if "fears_shared_after" not in st.session_state:
    st.session_state.fears_shared_after = None
if "hopes_shared_after" not in st.session_state:
    st.session_state.hopes_shared_after = None
if "last_scrolled_task_id" not in st.session_state:
    st.session_state.last_scrolled_task_id = None
if "detail_open_token" not in st.session_state:
    st.session_state.detail_open_token = 0
if "last_detail_scroll_token" not in st.session_state:
    st.session_state.last_detail_scroll_token = -1

# Keep viewport position consistent when switching between survey views/sub-views.
_view_anchor = (
    st.session_state.page,
    st.session_state.page6_question_index if st.session_state.page == 6 else None,
    st.session_state.pair_index if st.session_state.page == 7 else None,
)
_view_anchor_id = f"hf-view-anchor-{_view_anchor[0]}-{_view_anchor[1]}-{_view_anchor[2]}"
if "last_view_anchor" not in st.session_state:
    st.session_state.last_view_anchor = _view_anchor
elif st.session_state.last_view_anchor != _view_anchor:
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
                    if (!scrollToAnchor()) {
                        goTopFallback();
                    }
                }

                requestAnimationFrame(applyAnchor);
                setTimeout(applyAnchor, 60);
            })();
        </script>
        """.replace("__ANCHOR__", _view_anchor_id),
        height=0,
    )
    st.session_state.last_view_anchor = _view_anchor

# Fallback roles used only if DB occupations are unavailable.
default_job_roles = [
    "Software Engineer",
    "Data Analyst",
    "Teacher/Educator",
    "Healthcare Professional",
    "Business Manager",
    "Marketing Professional",
    "Customer Service Representative",
    "Content Writer",
    "Graphic Designer",
    "Project Manager"
]
_db_job_roles = load_job_roles() if st.session_state.page >= 1 else []
job_roles = _db_job_roles if _db_job_roles else default_job_roles

# AI Agent Definition
ai_agent_definition = """AI Agents are systems that can plan, act, and collaborate with humans to complete digital tasks autonomously. They can analyse information, generate content, make recommendations, and communicate in natural language, often adapting their actions based on feedback or changing goals.

In education, AI Agents might:
• Generate lesson plans tailored to different student levels,
• Provide instant feedback on written assignments,
• Monitor student progress and recommend support materials,
• Assist teachers with grading or administrative work.

In this study, we're interested in your views on which of these kinds of tasks you would prefer to keep doing yourself and which you might allow an AI Agent to handle."""

# Task Automation Gallery Mock Data
tasks_gallery = [
    {
        "id": 1,
        "title": "Process correspondence and paperwork",
        "risk_level": "HIGH",
        "automation_level": "HIGH",
        "description": "Process all correspondence and paperwork related to accounts.",
        "capability": "Document processing and automated correspondence management systems can fully handle standardized communications, form completion, and administrative paperwork with minimal human oversight.",
        "example_tech": "AI-powered CRM systems like Salesforce Einstein or HubSpot AI can automatically process, categorize, and respond to routine correspondence.",
        "dimensions": ["Mental", "Individual", "Routine", "Easy"],
        "risk_analysis": "High risk due to potential errors in automated correspondence that could damage professional relationships. AI may misinterpret context or tone, leading to inappropriate responses. Requires careful monitoring and human oversight for complex communications."
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
        "risk_analysis": "Low risk as AI-generated lesson plans can be reviewed and customized by teachers. The technology enhances efficiency while maintaining educational quality and teacher expertise."
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
        "risk_analysis": "Medium risk as scheduling conflicts or misinterpretations of availability could occur. However, most scheduling issues are recoverable and AI can significantly reduce coordination overhead."
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
        "risk_analysis": "Low risk as AI analytics provide data-driven insights that complement teacher judgment. Teachers retain final decision-making authority while benefiting from comprehensive data analysis."
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
        "risk_analysis": "Medium risk due to potential miscommunication from AI-generated content. Tone, context, and nuanced language may not be perfectly captured, requiring human review for important communications."
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
        "risk_analysis": "Medium risk as AI-generated content may lack depth or contain inaccuracies. Educational content requires accuracy and pedagogical expertise, so human review and customization are essential."
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
        "risk_analysis": "High risk due to the subjective nature of assessment and potential bias in AI grading algorithms. Student grades significantly impact educational and career opportunities, requiring human judgment."
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
        "risk_analysis": "Low risk as AI monitoring serves as an early warning system that enhances teacher effectiveness. Teachers can intervene based on AI alerts while maintaining oversight of student development."
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
        "risk_analysis": "High risk due to potential false positives/negatives in content detection. Over-moderation can suppress valid expression, while under-moderation can allow harmful content. Requires careful algorithm tuning and human oversight."
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
        "risk_analysis": "Low risk as AI tutoring supplements rather than replaces human instruction. Students benefit from 24/7 access to practice and immediate feedback while teachers focus on complex learning needs."
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
        "risk_analysis": "Low risk as data entry is highly automatable with minimal consequences for errors. AI can achieve higher accuracy than manual entry while freeing humans for more valuable tasks."
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
        "risk_analysis": "Medium risk as curriculum design requires deep pedagogical knowledge and cultural context. AI can assist but cannot replace the expertise needed for comprehensive educational program development."
    },
]

# Replace with DB tasks if available
_db_tasks = load_tasks(st.session_state.get("job_role")) if st.session_state.page >= 4 else []
if _db_tasks:
    tasks_gallery = _db_tasks

_db_pairs_preview = load_task_pairs() if st.session_state.page >= 7 else []
_runtime_db = get_runtime_db_status() if st.session_state.page >= 1 else {"connected": False, "database": "unknown", "error": ""}
_task_gallery_source = "DB" if _db_tasks else "MOCK"
_task_pairs_source = "DB" if _db_pairs_preview else "MOCK"
_db_state_text = get_runtime_db_display_text(_runtime_db)
_db_state_bg = "#ecfdf5" if _runtime_db["connected"] else "#fef2f2"
_db_state_border = "#16a34a" if _runtime_db["connected"] else "#dc2626"

if st.session_state.page >= 1:
    st.markdown(
        f"""
        <div style='margin: 6px 0 14px 0; padding: 10px 12px; border-radius: 8px;
                    border: 1px solid {_db_state_border}; background: {_db_state_bg}; font-size: 13px;'>
            <strong>Runtime Data Source</strong><br>
            DB: {_db_state_text} | Task Gallery: {_task_gallery_source} | Task Pairs: {_task_pairs_source}
        </div>
        """,
        unsafe_allow_html=True,
    )

# PAGE 0: Consent Form
if st.session_state.page == 0:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='max-width: 900px'>
    <h1 style='font-weight: bold; font-size: 24px;'>Participant Information and Consent Form</h1>
    </div>
    """, unsafe_allow_html=True)

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
    consent_read = st.checkbox("I have read and understood the information provided above.", key="consent_read")
    consent_age = st.checkbox("I confirm that I am at least 18 years old.", key="consent_age")
    consent_participate = st.checkbox("I voluntarily agree to participate in this study.", key="consent_participate")

    col_empty, col_start = st.columns([0.75, 0.25])
    with col_start:
        if st.button("Proceed to survey →", key="consent_next"):
            if consent_read and consent_age and consent_participate:
                st.session_state.page = 1
                st.rerun()
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

# PAGE 1: Prolific ID + Job Role Collection
elif st.session_state.page == 1:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='max-width: 800px'>
    <h1 style='font-weight: bold; font-size: 20px;'>WE ARE EXPLORING THE DIFFERENT FEARS AND HOPES PEOPLE HAVE ABOUT AI AGENTS</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    In this survey, you will be asked to:

    - Task 1: Share your fears and hopes about AI Agents.
    - Task 2: Explore a Task Automation Gallery showing how AI agents may support or replace parts of your work.
    - Task 3: Provide a brief evaluation of the visualization.
    
    All questions in this survey are mandatory. Read each of them thoroughly and provide your responses to the best of your ability. 
    Copying responses from external sources is not permitted and disabled.
    """)
    
    st.markdown("---")
    
    # Prolific ID input
    st.markdown("**Please enter your Prolific ID**")
    prolific_id = st.text_input("Prolific ID", value=st.session_state.prolific_id, key="prolific_input")
    
    # Job Role selection
    st.markdown("**What is your occupation?**")
    job_role_options = [""] + job_roles
    job_role_index = 0
    if st.session_state.job_role in job_role_options:
        job_role_index = job_role_options.index(st.session_state.job_role)

    job_role = st.selectbox(
        "Select your job role:",
        job_role_options,
        index=job_role_index,
        format_func=lambda x: "Please select your job role" if x == "" else x,
        key="job_input",
    )
    
    # Navigation
    col_prev1, col_dummy1, col_next1 = st.columns([0.2, 0.65, 0.15])
    with col_prev1:
        if st.button("← Previous", key="page1_prev"):
            st.session_state.page = 0
            st.rerun()
    with col_next1:
        if st.button("Next →", key="page1_next"):
            if not prolific_id.strip():
                st.error("Please enter your Prolific ID")
            elif not job_role:
                st.error("Please select your job role")
            else:
                st.session_state.prolific_id = prolific_id
                st.session_state.job_role = job_role

                db = SessionLocal()
                participant_id = get_or_create_participant(db, prolific_id, job_role)
                db.close()
                st.session_state.participant_id = participant_id

                st.session_state.page = 2
                st.rerun()

# PAGE 2: AI Definition + Description
elif st.session_state.page == 2:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='max-width: 800px'>
    <h1 style='font-weight: bold; font-size: 18px;'>THANK YOU FOR YOUR PERSPECTIVE. FOR THIS STUDY, WE'RE USING THE FOLLOWING DEFINITION OF AI AGENTS:</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("⚠️ UPDATE: Agent definition to be displayed here")
    
    st.markdown("---")
    
    st.markdown("**[AI Agent Definition]**")
    st.markdown(ai_agent_definition)
    
    st.markdown("---")
    
    st.markdown("**How would you describe Artificial Intelligence (AI) Agents to a friend?**")
    
    ai_description = st.text_area(
        "AI description",
        value=st.session_state.ai_description,
        height=120,
        placeholder="Enter your description here...",
        key="ai_desc_input"
    )
    
    st.markdown(f"**{len(ai_description)}/350 (Min. 70 characters)**")
    
    # Navigation
    col_prev2, col_dummy2, col_next2 = st.columns([0.2, 0.65, 0.15])
    with col_prev2:
        if st.button("← Previous", key="page2_prev"):
            st.session_state.page = 1
            st.rerun()
    with col_next2:
        if st.button("Next →", key="page2_next"):
            if len(ai_description.strip()) < 70:
                st.error("Please enter at least 70 characters")
            elif len(ai_description) > 350:
                st.error("Your response exceeds 350 characters")
            else:
                st.session_state.ai_description = ai_description

                if st.session_state.participant_id is not None:
                    db = SessionLocal()
                    save_profile(db, st.session_state.participant_id)
                    db.close()

                st.session_state.page = 3
                st.rerun()

# PAGE 3: Fears and Hopes Collection
elif st.session_state.page == 3:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    # Header with red banner styling
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US ABOUT</h2>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>YOUR FEARS AND HOPES</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Two-column layout
    left_col, right_col = st.columns(2, gap="large")
    
    # LEFT COLUMN - FEARS
    with left_col:
        st.markdown("""
        <div style='background-color: #1a1a1a; color: white; padding: 30px; border-radius: 8px;'>
        <h3 style='text-align: center; margin-bottom: 20px;'>I rate my fears about AI Agents as</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Fear rating slider
        fears_rating = st.slider(
            label="Fear Level",
            min_value=1,
            max_value=5,
            value=min(max(st.session_state.fears_rating, 1), 5),
            step=1,
            label_visibility="collapsed",
            key="fears_slider"
        )
        
        # Fear level labels
        st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: -25px;'>
            <span style='font-size: 12px; color: #666;'>No fear at all</span>
            <span style='font-size: 12px; color: #666;'>Terrified</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("**I fear AI Agents because...**")
        
        # Fear text input
        fears_text = st.text_area(
            label="Fear description",
            value=st.session_state.fears_text,
            height=100,
            placeholder="Write your fears here",
            label_visibility="collapsed",
            key="fears_input"
        )
        
        st.markdown(f"**{len(fears_text)}/350 (Min. 70 characters)**")
        
        st.markdown("")
        st.markdown("**To what extent do you believe that your AI Agents fear is shared by most people?**")
        
        # Fear sharing - slider
        fear_sharing_options = ["", "Not at all", "Rarely", "Occasionally", "Moderately", "Often", "Very often", "Almost always"]
        fears_shared = st.select_slider(
            label="Fear shared",
            options=fear_sharing_options,
            value=st.session_state.fears_shared if st.session_state.fears_shared in fear_sharing_options else "",
            label_visibility="collapsed",
            key="fears_shared_input"
        )
    
    # RIGHT COLUMN - HOPES
    with right_col:
        st.markdown("""
        <div style='border: 2px solid #333; padding: 30px; border-radius: 8px; background-color: white;'>
        <h3 style='text-align: center; margin-bottom: 20px; color: black;'>I rate my hopes about AI Agents as</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Hope rating slider
        hopes_rating = st.slider(
            label="Hope Level",
            min_value=1,
            max_value=5,
            value=min(max(st.session_state.hopes_rating, 1), 5),
            step=1,
            label_visibility="collapsed",
            key="hopes_slider"
        )
        
        # Hope level labels
        st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: -25px;'>
            <span style='font-size: 12px; color: #666;'>No hope at all</span>
            <span style='font-size: 12px; color: #666;'>Full of hope</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("**I have hope in AI Agents because...**")
        
        # Hope text input
        hopes_text = st.text_area(
            label="Hope description",
            value=st.session_state.hopes_text,
            height=100,
            placeholder="Write your hopes here",
            label_visibility="collapsed",
            key="hopes_input"
        )
        
        st.markdown(f"**{len(hopes_text)}/350 (Min. 70 characters)**")
        
        st.markdown("")
        st.markdown("**To what extent do you believe that your AI Agents hopes are shared by most people?**")
        
        # Hope sharing - slider
        hope_sharing_options = ["", "Not at all", "Rarely", "Occasionally", "Moderately", "Often", "Very often", "Almost always"]
        hopes_shared = st.select_slider(
            label="Hope shared",
            options=hope_sharing_options,
            value=st.session_state.hopes_shared if st.session_state.hopes_shared in hope_sharing_options else "",
            label_visibility="collapsed",
            key="hopes_shared_input"
        )
    
    # Navigation
    st.markdown("---")
    col_prev3, col_dummy3, col_next3 = st.columns([0.2, 0.65, 0.15])
    with col_prev3:
        if st.button("← Previous", key="page3_prev"):
            st.session_state.page = 2
            st.rerun()
    with col_next3:
        if st.button("Next →", key="page3_next"):
            if len(fears_text.strip()) < 70:
                st.error("Fears: Please enter at least 70 characters")
            elif len(fears_text) > 350:
                st.error("Fears: Your response exceeds 350 characters")
            elif len(hopes_text.strip()) < 70:
                st.error("Hopes: Please enter at least 70 characters")
            elif len(hopes_text) > 350:
                st.error("Hopes: Your response exceeds 350 characters")
            elif not fears_shared:
                st.error("Fears: Please select how widely your fear is shared")
            elif not hopes_shared:
                st.error("Hopes: Please select how widely your hope is shared")
            else:
                st.session_state.fears_rating = fears_rating
                st.session_state.hopes_rating = hopes_rating
                st.session_state.fears_text = fears_text
                st.session_state.hopes_text = hopes_text
                st.session_state.fears_shared = fears_shared
                st.session_state.hopes_shared = hopes_shared

                if st.session_state.participant_id is not None:
                    db = SessionLocal()
                    save_attitude(
                        db,
                        st.session_state.participant_id,
                        st.session_state.ai_description,
                        fears_rating,
                        fears_text,
                        fears_shared,
                        hopes_rating,
                        hopes_text,
                        hopes_shared,
                    )
                    db.close()

                st.session_state.page = 4
                st.rerun()

# PAGE 4: Task Automation Gallery
elif st.session_state.page == 4:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 40px;'>
        <div style='display: flex; justify-content: center; align-items: center; gap: 28px; flex-wrap: wrap; margin-bottom: 8px;'>
            <h2 style='margin: 0; font-weight: bold; letter-spacing: 2px; color: #E63946;'>WHOSE FEARS?</h2>
            <h2 style='margin: 0; font-weight: bold; letter-spacing: 2px; color: #43AA8B;'>WHOSE HOPES?</h2>
        </div>
        <h1 style='font-size: 28px; font-weight: bold; margin-top: 20px;'>TASK AUTOMATION GALLERY</h1>
        <p style='color: #666; margin-top: 10px;'>Click and read about your job automation potential</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Modal for task details
    if st.session_state.selected_task is not None:
        # Guarantee every View Details click scrolls to the expanded detail header.
        if st.session_state.last_detail_scroll_token != st.session_state.detail_open_token:
            st.session_state.last_detail_scroll_token = st.session_state.detail_open_token
            components.html(
                """
                <script>
                    (function () {
                        const w = window.parent;
                        const doc = w.document;
                        function jumpToDetailTop() {
                            const detailTop = doc.getElementById("hf-task-detail-top");
                            if (detailTop) {
                                detailTop.scrollIntoView({ block: "start", inline: "nearest", behavior: "auto" });
                                return;
                            }
                            const main = doc.querySelector("[data-testid='stAppViewContainer'] > .main");
                            w.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                            if (main) main.scrollTop = 0;
                        }

                        jumpToDetailTop();
                        let count = 0;
                        const timer = setInterval(() => {
                            jumpToDetailTop();
                            count += 1;
                            if (count >= 6) clearInterval(timer);
                        }, 40);
                    })();
                </script>
                """,
                height=0,
            )
        task = next((t for t in tasks_gallery if t["id"] == st.session_state.selected_task), None)
        if task:
            # Determine color based on risk level
            if task['risk_level'] == "HIGH":
                header_color = "#E63946"
            elif task['risk_level'] == "MEDIUM":
                header_color = "#F4A000"
            else:
                header_color = "#43AA8B"
            
            col1, col2, col3 = st.columns([0.05, 0.9, 0.05])
            with col2:
                st.markdown("<div id='hf-task-detail-top' style='height:1px; margin:0; padding:0; scroll-margin-top:72px;'></div>", unsafe_allow_html=True)
                # Header with task title and close button
                st.markdown(f"""
                <div style='background: {header_color}; color: white; padding: 25px 30px; border-radius: 8px; 
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;'>
                    <h2 style='margin: 0; font-size: 20px; font-weight: 700;'>{task['title']}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Close button positioned inside content area
                col_close1, col_close2 = st.columns([0.9, 0.1])
                with col_close2:
                    if st.button("✕", key="close_modal"):
                        if st.session_state.participant_id is not None:
                            db = SessionLocal()
                            try:
                                record_task_event(db, st.session_state.participant_id, task["id"], "close")
                            finally:
                                db.close()
                        st.session_state.selected_task = None
                        st.rerun()
                
                # Risk level badge
                if task['risk_level'] == "HIGH":
                    color = "#E63946"
                    risk_text = "HIGH RISK"
                elif task['risk_level'] == "MEDIUM":
                    color = "#F4D35E"
                    risk_text = "MEDIUM RISK"
                else:
                    color = "#43AA8B"
                    risk_text = "LOW RISK"
                
                st.markdown(f"""
                <div style='background: {color}; color: white; padding: 8px 12px; border-radius: 4px; display: inline-block; margin: 10px 0;'>
                    <strong>{risk_text}</strong>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("")
                st.markdown(f"**AI CAPABILITY:** {task['capability']}")
                
                st.markdown("")
                st.markdown(f"**EXAMPLE TECHNOLOGY:** {task['example_tech']}")
                
                st.markdown("")
                st.markdown("**RISK ANALYSIS:**")
                st.markdown(task['risk_analysis'])
                
                st.markdown("")
                st.markdown("**Task Dimensions:**")
                
                # Task dimensions with emojis
                dimensions_emojis = {
                    "Mental": "🧠",
                    "Individual": "👤",
                    "Routine": "📋",
                    "Easy": "😊"
                }
                
                cols = st.columns(len(task['dimensions']))
                for idx, dim in enumerate(task['dimensions']):
                    with cols[idx]:
                        st.markdown(f"{dimensions_emojis.get(dim, '')} {dim}")
                
                st.markdown("")
                if st.button("More →", key=f"task_more_{task['id']}"):
                    if st.session_state.participant_id is not None:
                        db = SessionLocal()
                        try:
                            record_task_event(db, st.session_state.participant_id, task["id"], "open_more")
                        finally:
                            db.close()
                    st.session_state.selected_task = None
                    st.rerun()
    else:
        st.session_state.last_scrolled_task_id = None
    
    # Task gallery in 5 columns with serpentine (Z-shape) placement.
    # Tasks are globally ordered from HIGH -> MEDIUM -> LOW risk (red -> green).
    st.markdown("---")
    risk_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    ordered_tasks = sorted(
        tasks_gallery,
        key=lambda t: (risk_rank.get(t.get("risk_level"), 1), t.get("id", 0)),
    )

    n_cols = 5
    n_rows = max(1, (len(ordered_tasks) + n_cols - 1) // n_cols)
    columns_tasks = [[None for _ in range(n_rows)] for _ in range(n_cols)]

    for i, task in enumerate(ordered_tasks):
        col_i = i // n_rows
        pos_in_col = i % n_rows
        if col_i >= n_cols:
            break

        if col_i % 2 == 0:
            row_i = pos_in_col  # top -> bottom
        else:
            row_i = n_rows - 1 - pos_in_col  # bottom -> top

        columns_tasks[col_i][row_i] = task

    def risk_color(level):
        if level == "HIGH":
            return "#E63946"
        if level == "MEDIUM":
            return "#F4A000"
        return "#43AA8B"
    
    # Add global CSS for hover effects and transitions
    st.markdown("""
    <style>
    .task-card-wrapper {
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    
    .task-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
    }
    
    .task-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .risk-gradient-hint {
        margin: 0 0 14px 0;
        padding: 8px 12px;
        border-radius: 8px;
        background: linear-gradient(90deg, #E63946 0%, #F4A000 50%, #43AA8B 100%);
        color: #fff;
        font-weight: 700;
        text-align: center;
        letter-spacing: 0.2px;
        font-size: 12px;
    }

    /* Improve button styling */
    .stButton > button {
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 6px;
        transition: all 0.2s ease;
        width: 100%;
        font-size: 14px;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='risk-gradient-hint'>RED → GREEN (serpentine layout)</div>", unsafe_allow_html=True)

    def render_task_cell(task):
        color = risk_color(task.get("risk_level"))
        risk_text = task.get("risk_level", "MEDIUM")
        st.markdown(
            f"""
            <div class='task-card-wrapper'>
                <div class='task-card' style='background: linear-gradient(135deg, {color} 0%, {color} 100%);
                     color: white; padding: 18px; border-radius: 8px; min-height: 98px;
                     display: flex; align-items: center; justify-content: center; text-align: center;'>
                    <div style='font-weight: 700; font-size: 13px; line-height: 1.3;'>
                        {task['title']}<br>
                        <span style='font-size: 11px; opacity: 0.9;'>[{risk_text}]</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(label="📖 View Details", key=f"task_{task['id']}", use_container_width=True):
            st.session_state.selected_task = task['id']
            st.session_state.detail_open_token += 1
            if st.session_state.participant_id is not None:
                db = SessionLocal()
                try:
                    record_task_event(db, st.session_state.participant_id, task['id'], "view")
                finally:
                    db.close()
            st.rerun()

    cols5 = st.columns(n_cols, gap="small")
    for col_i in range(n_cols):
        with cols5[col_i]:
            for task in columns_tasks[col_i]:
                if task is not None:
                    render_task_cell(task)
    
    st.markdown("---")
    
    # Navigation
    col_prev4, col_dummy4, col_next4 = st.columns([0.2, 0.65, 0.15])
    with col_prev4:
        if st.button("← Previous", key="page4_prev"):
            st.session_state.page = 3
            st.rerun()
    with col_next4:
        if st.button("Next →", key="page4_next"):
            st.session_state.page = 5
            st.rerun()

# PAGE 5: Demographic information (ParticipantProfile)
elif st.session_state.page == 5:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US ABOUT YOURSELF</h2>
        <p>Please provide a few demographic details so we can better understand participant background.</p>
    </div>
    """, unsafe_allow_html=True)

    if "age_group" not in st.session_state:
        st.session_state.age_group = ""
    if "gender_identity" not in st.session_state:
        st.session_state.gender_identity = ""
    if "gender_other" not in st.session_state:
        st.session_state.gender_other = ""
    if "ethnicity" not in st.session_state:
        st.session_state.ethnicity = ""
    if "ethnicity_other" not in st.session_state:
        st.session_state.ethnicity_other = ""
    if "favourite_colour" not in st.session_state:
        st.session_state.favourite_colour = ""
    if "favourite_colour_other" not in st.session_state:
        st.session_state.favourite_colour_other = ""
    if "education_level" not in st.session_state:
        st.session_state.education_level = ""
    if "education_other" not in st.session_state:
        st.session_state.education_other = ""


    age_options = [
        "",
        "Under 18",
        "18-24 years old",
        "25-34 years old",
        "35-44 years old",
        "45-54 years old",
        "55-64 years old",
        "65+ years old",
    ]
    gender_options = ["", "Female", "Male", "Nonbinary", "Transgender", "Prefer not to say", "Other"]
    ethnicity_options = ["", "American Indian or Alaska Native", "Asian or Pacific Islander", "Black or African American", "Hispanic or Latinx", "Middle Eastern or North African", "White", "Multiethnic", "Other"]
    colour_options = ["", "Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"]
    education_options = ["", "Less than High School", "High School", "Some college (no degree)", "Technical Certification", "Associate degree (2-year)", "Bachelor's degree (4-year)", "Master's degree", "Doctoral degree", "Professional degree (JD, MD)", "Other"]

    st.selectbox(
        "What is your age group?",
        age_options,
        index=age_options.index(st.session_state.age_group) if st.session_state.age_group in age_options else 0,
        format_func=lambda x: "Please select" if x == "" else x,
        key="age_group",
    )
    gender_selected = st.selectbox(
        "What is your gender identity?",
        gender_options,
        index=gender_options.index(st.session_state.gender_identity) if st.session_state.gender_identity in gender_options else 0,
        format_func=lambda x: "Please select" if x == "" else x,
        key="gender_identity",
    )
    if gender_selected == "Other":
        st.text_input("Please specify", value=st.session_state.gender_other, key="gender_other")
    ethnicity_selected = st.selectbox(
        "Which ethnicity best describes you?",
        ethnicity_options,
        index=ethnicity_options.index(st.session_state.ethnicity) if st.session_state.ethnicity in ethnicity_options else 0,
        format_func=lambda x: "Please select" if x == "" else x,
        key="ethnicity",
    )
    if ethnicity_selected == "Other":
        st.text_input("Please specify", value=st.session_state.ethnicity_other, key="ethnicity_other")
    st.selectbox(
        "What is your favourite colour? (This is an attention check question. Please choose red.)",
        colour_options,
        index=colour_options.index(st.session_state.favourite_colour) if st.session_state.favourite_colour in colour_options else 0,
        format_func=lambda x: "Please select" if x == "" else x,
        key="favourite_colour",
    )
    education_selected = st.selectbox(
        "What is your highest level of education?",
        education_options,
        index=education_options.index(st.session_state.education_level) if st.session_state.education_level in education_options else 0,
        format_func=lambda x: "Please select" if x == "" else x,
        key="education_level",
    )
    if education_selected == "Other":
        st.text_input("Please specify", value=st.session_state.education_other, key="education_other")
    
    
    col_prev5, col_dummy5, col_next5 = st.columns([0.2, 0.65, 0.15])
    with col_prev5:
        if st.button("← Previous", key="page5_prev"):
            st.session_state.page = 4
            st.rerun()
    with col_next5:
        if st.button("Next →", key="page5_next"):
            # Validate required fields
            if not st.session_state.age_group:
                st.error("Please fill out your age group")
            elif not st.session_state.gender_identity:
                st.error("Please fill out your gender identity")
            elif st.session_state.gender_identity == "Other" and not st.session_state.gender_other.strip():
                st.error("Please specify your gender identity")
            elif not st.session_state.ethnicity:
                st.error("Please fill out your ethnicity")
            elif st.session_state.ethnicity == "Other" and not st.session_state.ethnicity_other.strip():
                st.error("Please specify your ethnicity")
            elif not st.session_state.favourite_colour.strip():
                st.error("Please fill out your favourite colour")
            elif not st.session_state.education_level:
                st.error("Please fill out your education level")
            elif st.session_state.education_level == "Other" and not st.session_state.education_other.strip():
                st.error("Please specify your education level")
            else:
                # Prepare final values
                final_gender = st.session_state.gender_other if st.session_state.gender_identity == "Other" else st.session_state.gender_identity
                final_ethnicity = st.session_state.ethnicity_other if st.session_state.ethnicity == "Other" else st.session_state.ethnicity
                final_education = st.session_state.education_other if st.session_state.education_level == "Other" else st.session_state.education_level

                if st.session_state.participant_id is not None:
                    db = SessionLocal()
                    save_profile(
                        db,
                        st.session_state.participant_id,
                        age_group=st.session_state.age_group,
                        gender_identity=final_gender,
                        ethnicity=final_ethnicity,
                        favourite_colour=st.session_state.favourite_colour,
                        education_level=final_education,
                    )
                    db.close()
                st.session_state.page6_question_index = 0
                st.session_state.page = 6
                st.rerun()

# PAGE 6: AI Behavior and Profession Information
elif st.session_state.page == 6:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>YOUR EXPERIENCE WITH AI</h2>
        <p>Please rate your agreement with the following statements about your occupation and AI usage.</p>
    </div>
    """, unsafe_allow_html=True)

    likert_scale_options = ["Strongly Disagree", "Disagree", "Somewhat Disagree", "Neutral", "Somewhat Agree", "Agree", "Strongly Agree"]
    likert_options = [""] + likert_scale_options
    likert_values = {opt: i for i, opt in enumerate(likert_scale_options)}

    # Initialize likelihood question states
    for key in ["smart_devices", "ai_help", "ai_tech_id", "ai_skillful", "ai_learning",
                "ai_efficiency", "ai_eval", "ai_solution", "attention_check", "ai_choice",
                "ethical", "privacy", "ai_abuse"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    # Maintain page-level index to show one question per sub-page
    if "page6_question_index" not in st.session_state:
        st.session_state.page6_question_index = 0

    page6_questions = [
        {
            "type": "occupation_fit",
            "text": "Which description best fits your occupation?",
            "key": "occupation_fit_radio",
            "options": [
                "",
                "My occupation requires minimal prior experience or training, potentially needs a high school diploma or GED, and typically involves a brief training period of a few days to a few months.",
                "My occupation requires a high school diploma, several months to a year of training, and often involve assisting others.",
                "My occupation requires vocational training, a college degree, or specialized certifications, and typically involves complex problem-solving, creativity, or advanced technical skills."
            ]
        },
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
        {"type": "likert", "text": "I am always alert to the abuse of AI technology", "key": "ai_abuse"}
    ]
    st.session_state.page6_total_questions = len(page6_questions)

    idx = st.session_state.page6_question_index
    current_question = page6_questions[idx]

    st.markdown(f"**Question {idx + 1}/{len(page6_questions)}**")
    if current_question["type"] == "occupation_fit":
        st.markdown(f"**{current_question['text']}**")
        st.selectbox(
            "Select the best fit:",
            current_question["options"],
            format_func=lambda x: "Please select" if x == "" else x,
            key="occupation_fit_radio"
        )
    else:
        if current_question["key"] not in st.session_state:
            st.session_state[current_question["key"]] = ""

        display_text = current_question["text"]
        if current_question["key"] == "attention_check":
            display_text = "⚠️ " + display_text

        st.markdown(f"**{display_text}**")
        st.session_state[current_question["key"]] = st.select_slider(
            "",
            options=likert_options,
            value=st.session_state[current_question["key"]] if st.session_state[current_question["key"]] in likert_options else "",
            label_visibility="collapsed",
            key=f"{current_question['key']}_slider"
        )

    st.markdown("---")
    col_prev, col_dummy, col_next = st.columns([0.2, 0.6, 0.2])
    with col_prev:
        if idx > 0:
            if st.button("← Previous", key="page6_prev"):
                st.session_state.page6_question_index = idx - 1
                st.rerun()
        else:
            if st.button("← Previous", key="page6_prev_page"):
                st.session_state.page = 5
                st.rerun()

    with col_next:
        next_label = "Finish →" if idx == len(page6_questions) - 1 else "Next →"
        if st.button(next_label, key="page6_next"):
            if current_question["type"] == "occupation_fit":
                if not st.session_state.get("occupation_fit_radio"):
                    st.error("Please select the description that best fits your occupation")
                    st.stop()
            else:
                if not st.session_state.get(current_question["key"]):
                    st.error("Please select one option before continuing")
                    st.stop()

            if idx < len(page6_questions) - 1:
                st.session_state.page6_question_index = idx + 1
                st.rerun()
            else:
                attention_value = likert_values[st.session_state["attention_check"]]
                if attention_value >= 2:
                    st.error("⚠️ Attention check: Your response to the AI squirrels question suggests you may not be answering carefully. Please review your responses.")
                    st.stop()

                _occ_options = [
                    "My occupation requires minimal prior experience or training, potentially needs a high school diploma or GED, and typically involves a brief training period of a few days to a few months.",
                    "My occupation requires a high school diploma, several months to a year of training, and often involve assisting others.",
                    "My occupation requires vocational training, a college degree, or specialized certifications, and typically involves complex problem-solving, creativity, or advanced technical skills."
                ]
                occupation_fit_choice = st.session_state.get("occupation_fit_radio", _occ_options[0])
                if occupation_fit_choice not in _occ_options:
                    occupation_fit_choice = _occ_options[0]

                db = SessionLocal()
                save_profile(
                    db,
                    st.session_state.participant_id,
                    occupation_description=occupation_fit_choice,
                )
                save_ai_behavior(
                    db,
                    st.session_state.participant_id,
                    occupation_fit=_occ_options.index(occupation_fit_choice),
                    smart_devices_recognition=likert_values[st.session_state["smart_devices"]],
                    ai_help_uncertainty=likert_values[st.session_state["ai_help"]],
                    ai_technology_identification=likert_values[st.session_state["ai_tech_id"]],
                    ai_skillful_use=likert_values[st.session_state["ai_skillful"]],
                    ai_learning_difficulty=likert_values[st.session_state["ai_learning"]],
                    ai_work_efficiency=likert_values[st.session_state["ai_efficiency"]],
                    ai_capabilities_evaluation=likert_values[st.session_state["ai_eval"]],
                    ai_solution_choice=likert_values[st.session_state["ai_solution"]],
                    attention_check=attention_value,
                    ai_application_choice=likert_values[st.session_state["ai_choice"]],
                    ethical_compliance=likert_values[st.session_state["ethical"]],
                    privacy_alertness=likert_values[st.session_state["privacy"]],
                    ai_abuse_alertness=likert_values[st.session_state["ai_abuse"]],
                )
                db.close()
                st.session_state.page = 7
                st.session_state.pair_index = 0
                st.rerun()

# PAGE 7: Task Pair Choices
elif st.session_state.page == 7:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US WHAT KIND OF WORKER YOU ARE</h2>
        <p style='font-size: 18px; font-weight: bold;'>Imagine it's 10 years from now.<br>What tasks do you wish to do yourself and not be done by an Agent?</p>
    </div>
    """, unsafe_allow_html=True)

    # Load task pairs from DB, fallback to mock if empty
    _db_pairs = load_task_pairs()
    mock_pairs = [
        {"pair_id": -1,  "left": {"task_id": 2,  "title": "Generate lesson plans",            "description": "Generate lesson plans tailored to different student levels."},
                         "right": {"task_id": 1,  "title": "Process correspondence",             "description": "Process all correspondence and paperwork related to accounts."}},
        {"pair_id": -2,  "left": {"task_id": 5,  "title": "Write emails",                       "description": "Compose and send routine emails."},
                         "right": {"task_id": 3,  "title": "Schedule meetings",                   "description": "Schedule and coordinate meetings across teams."}},
        {"pair_id": -3,  "left": {"task_id": 7,  "title": "Grade assignments",                   "description": "Grade assignments and provide feedback."},
                         "right": {"task_id": 4,  "title": "Analyze student performance",         "description": "Analyze student performance data and generate insights."}},
        {"pair_id": -4,  "left": {"task_id": 6,  "title": "Create content",                      "description": "Create educational content, summaries, and explanations."},
                         "right": {"task_id": 8,  "title": "Monitor student progress",            "description": "Monitor student progress and flag concerns."}},
        {"pair_id": -5,  "left": {"task_id": 10, "title": "Personalized tutoring",               "description": "Provide personalized tutoring and one-on-one support."},
                         "right": {"task_id": 9,  "title": "Content moderation",                  "description": "Moderate user-generated content and discussions."}},
        {"pair_id": -6,  "left": {"task_id": 11, "title": "Data entry",                          "description": "Enter data into systems and databases."},
                         "right": {"task_id": 12, "title": "Curriculum design",                   "description": "Design and develop new curricula."}},
    ]
    task_pairs = _db_pairs if _db_pairs else mock_pairs
    total_pairs = len(task_pairs)

    if st.session_state.pair_index >= total_pairs:
        # All pairs done → save and move to completion
        if st.session_state.participant_id is not None:
            db = SessionLocal()
            for pair_id, choice in st.session_state.pair_choices.items():
                if pair_id > 0:  # only save real DB pair_ids
                    save_task_pair_choice(db, st.session_state.participant_id, pair_id, choice)
            db.close()
        st.session_state.page = 8
        st.rerun()
    else:
        current_pair = task_pairs[st.session_state.pair_index]
        pair_id = current_pair["pair_id"]

        st.markdown(f"<div style='text-align:center; color:#888; margin-bottom:20px;'>{st.session_state.pair_index + 1}/{total_pairs}</div>", unsafe_allow_html=True)

        col_left, col_or, col_right = st.columns([0.45, 0.1, 0.45])
        with col_left:
            left_task = current_pair["left"]
            left_selected = st.session_state.pair_choices.get(pair_id) == "left"
            border_left = "3px solid #E63946" if left_selected else "2px solid #333"
            st.markdown(f"""
            <div style='border:{border_left}; padding:30px; border-radius:8px; min-height:160px; background:{'#fff5f5' if left_selected else 'white'};'>
                <strong>{left_task['title']}</strong>
                <p style='color:#555; font-size:14px; margin-top:10px;'>{left_task['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Choose this →", key=f"choose_left_{pair_id}"):
                st.session_state.pair_choices[pair_id] = "left"
                st.rerun()

        with col_or:
            st.markdown("""
            <div style='display:flex; align-items:center; justify-content:center; height:160px;'>
                <div style='background:#111; color:white; border-radius:50%; width:48px; height:48px;
                            display:flex; align-items:center; justify-content:center;
                            font-weight:bold; font-size:16px;'>or</div>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            right_task = current_pair["right"]
            right_selected = st.session_state.pair_choices.get(pair_id) == "right"
            border_right = "3px solid #E63946" if right_selected else "2px solid #333"
            st.markdown(f"""
            <div style='border:{border_right}; padding:30px; border-radius:8px; min-height:160px; background:{'#fff5f5' if right_selected else 'white'};'>
                <strong>{right_task['title']}</strong>
                <p style='color:#555; font-size:14px; margin-top:10px;'>{right_task['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Choose this →", key=f"choose_right_{pair_id}"):
                st.session_state.pair_choices[pair_id] = "right"
                st.rerun()

        st.markdown("---")
        col_prev7, col_dummy7, col_next7 = st.columns([0.24, 0.52, 0.24])
        with col_prev7:
            if st.button("← Previous", key="page7_prev"):
                if st.session_state.pair_index > 0:
                    st.session_state.pair_index -= 1
                else:
                    st.session_state.page = 6
                    total_q = st.session_state.get("page6_total_questions", 14)
                    st.session_state.page6_question_index = max(total_q - 1, 0)
                st.rerun()
        with col_dummy7:
            st.markdown("")
        with col_next7:
            next7_label = "Finish →" if st.session_state.pair_index == total_pairs - 1 else "Next →"
            _next_spacer, _next_btn_col = st.columns([0.35, 0.65])
            with _next_btn_col:
                if st.button(next7_label, key="page7_next"):
                    current_choice = st.session_state.pair_choices.get(pair_id)
                    if current_choice not in {"left", "right"}:
                        st.error("Please choose one task.")
                    else:
                        st.session_state.pair_index += 1
                        st.rerun()

# PAGE 8: Fears and Hopes Collection (After Survey)
elif st.session_state.page == 8:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>AFTER COMPLETING THE SURVEY</h2>
        <h2 style='font-weight: bold; letter-spacing: 2px;'>TELL US ABOUT YOUR FEARS AND HOPES</h2>
    </div>
    """, unsafe_allow_html=True)

    left_col_after, right_col_after = st.columns(2, gap="large")

    with left_col_after:
        st.markdown("""
        <div style='background-color: #1a1a1a; color: white; padding: 30px; border-radius: 8px;'>
        <h3 style='text-align: center; margin-bottom: 20px;'>I rate my fears about AI Agents as</h3>
        </div>
        """, unsafe_allow_html=True)

        fears_rating_after = st.slider(
            label="Fear Level After",
            min_value=1,
            max_value=5,
            value=min(max(st.session_state.fears_rating_after, 1), 5),
            step=1,
            label_visibility="collapsed",
            key="fears_after_slider"
        )

        st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: -25px;'>
            <span style='font-size: 12px; color: #666;'>No fear at all</span>
            <span style='font-size: 12px; color: #666;'>Terrified</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**I fear AI Agents because...**")

        fears_text_after = st.text_area(
            label="Fear description after",
            value=st.session_state.fears_text_after,
            height=100,
            placeholder="Write your fears here",
            label_visibility="collapsed",
            key="fears_after_input"
        )

        st.markdown(f"**{len(fears_text_after)}/350 (Min. 70 characters)**")

        st.markdown("")
        st.markdown("**To what extent do you believe that your AI Agents fear is shared by most people?**")

        fear_sharing_options_after = ["", "Not at all", "Rarely", "Occasionally", "Moderately", "Often", "Very often", "Almost always"]
        fears_shared_after = st.select_slider(
            label="Fear shared after",
            options=fear_sharing_options_after,
            value=st.session_state.fears_shared_after if st.session_state.fears_shared_after in fear_sharing_options_after else "",
            label_visibility="collapsed",
            key="fears_shared_after_input"
        )

    with right_col_after:
        st.markdown("""
        <div style='border: 2px solid #333; padding: 30px; border-radius: 8px; background-color: white;'>
        <h3 style='text-align: center; margin-bottom: 20px; color: black;'>I rate my hopes about AI Agents as</h3>
        </div>
        """, unsafe_allow_html=True)

        hopes_rating_after = st.slider(
            label="Hope Level After",
            min_value=1,
            max_value=5,
            value=min(max(st.session_state.hopes_rating_after, 1), 5),
            step=1,
            label_visibility="collapsed",
            key="hopes_after_slider"
        )

        st.markdown("""
        <div style='display: flex; justify-content: space-between; margin-top: -25px;'>
            <span style='font-size: 12px; color: #666;'>No hope at all</span>
            <span style='font-size: 12px; color: #666;'>Full of hope</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**I have hope in AI Agents because...**")

        hopes_text_after = st.text_area(
            label="Hope description after",
            value=st.session_state.hopes_text_after,
            height=100,
            placeholder="Write your hopes here",
            label_visibility="collapsed",
            key="hopes_after_input"
        )

        st.markdown(f"**{len(hopes_text_after)}/350 (Min. 70 characters)**")

        st.markdown("")
        st.markdown("**To what extent do you believe that your AI Agents hopes are shared by most people?**")

        hope_sharing_options_after = ["", "Not at all", "Rarely", "Occasionally", "Moderately", "Often", "Very often", "Almost always"]
        hopes_shared_after = st.select_slider(
            label="Hope shared after",
            options=hope_sharing_options_after,
            value=st.session_state.hopes_shared_after if st.session_state.hopes_shared_after in hope_sharing_options_after else "",
            label_visibility="collapsed",
            key="hopes_shared_after_input"
        )

    st.markdown("---")
    col_prev8, col_dummy8, col_next8 = st.columns([0.2, 0.65, 0.15])
    with col_prev8:
        if st.button("← Previous", key="page8_prev"):
            _pairs_for_back = load_task_pairs()
            _fallback_pairs_for_back = [
                {"pair_id": -1,  "left": {"task_id": 2,  "title": "Generate lesson plans",            "description": "Generate lesson plans tailored to different student levels."},
                                 "right": {"task_id": 1,  "title": "Process correspondence",             "description": "Process all correspondence and paperwork related to accounts."}},
                {"pair_id": -2,  "left": {"task_id": 5,  "title": "Write emails",                       "description": "Compose and send routine emails."},
                                 "right": {"task_id": 3,  "title": "Schedule meetings",                   "description": "Schedule and coordinate meetings across teams."}},
                {"pair_id": -3,  "left": {"task_id": 7,  "title": "Grade assignments",                   "description": "Grade assignments and provide feedback."},
                                 "right": {"task_id": 4,  "title": "Analyze student performance",         "description": "Analyze student performance data and generate insights."}},
                {"pair_id": -4,  "left": {"task_id": 6,  "title": "Create content",                      "description": "Create educational content, summaries, and explanations."},
                                 "right": {"task_id": 8,  "title": "Monitor student progress",            "description": "Monitor student progress and flag concerns."}},
                {"pair_id": -5,  "left": {"task_id": 10, "title": "Personalized tutoring",               "description": "Provide personalized tutoring and one-on-one support."},
                                 "right": {"task_id": 9,  "title": "Content moderation",                  "description": "Moderate user-generated content and discussions."}},
                {"pair_id": -6,  "left": {"task_id": 11, "title": "Data entry",                          "description": "Enter data into systems and databases."},
                                 "right": {"task_id": 12, "title": "Curriculum design",                   "description": "Design and develop new curricula."}},
            ]
            _all_pairs_for_back = _pairs_for_back if _pairs_for_back else _fallback_pairs_for_back
            st.session_state.pair_index = max(len(_all_pairs_for_back) - 1, 0)
            st.session_state.page = 7
            st.rerun()
    with col_next8:
        if st.button("Next →", key="page8_next"):
            if len(fears_text_after.strip()) < 70:
                st.error("Fears: Please enter at least 70 characters")
            elif len(fears_text_after) > 350:
                st.error("Fears: Your response exceeds 350 characters")
            elif len(hopes_text_after.strip()) < 70:
                st.error("Hopes: Please enter at least 70 characters")
            elif len(hopes_text_after) > 350:
                st.error("Hopes: Your response exceeds 350 characters")
            elif not fears_shared_after:
                st.error("Fears: Please select how widely your fear is shared")
            elif not hopes_shared_after:
                st.error("Hopes: Please select how widely your hope is shared")
            else:
                st.session_state.fears_rating_after = fears_rating_after
                st.session_state.hopes_rating_after = hopes_rating_after
                st.session_state.fears_text_after = fears_text_after
                st.session_state.hopes_text_after = hopes_text_after
                st.session_state.fears_shared_after = fears_shared_after
                st.session_state.hopes_shared_after = hopes_shared_after

                if st.session_state.participant_id is not None:
                    db = SessionLocal()
                    save_attitude_after(
                        db,
                        st.session_state.participant_id,
                        fears_rating_after,
                        fears_text_after,
                        fears_shared_after,
                        hopes_rating_after,
                        hopes_text_after,
                        hopes_shared_after,
                    )
                    db.close()

                st.session_state.page = 9
                st.rerun()

# PAGE 9: Completion message
elif st.session_state.page == 9:
    st.markdown(f"<div id='{_view_anchor_id}' data-hf-view-anchor='true' style='height:1px; margin:0; padding:0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; margin-top: 100px;'>
        <h2 style='font-weight: bold;'>Thank you!</h2>
        <p>Your responses have been recorded successfully.</p>
        <p>Please close this tab or wait while we redirect you.</p>
    </div>
    """, unsafe_allow_html=True)
