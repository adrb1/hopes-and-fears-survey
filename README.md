# Hopes and Fears Survey

This project is a Streamlit survey application used to collect participants' perceptions of AI Agents, including:

- baseline AI understanding and demographic profile,
- before/after fear and hope ratings,
- task preference choices between human and AI execution,
- interaction events in the task gallery.

The app uses SQLAlchemy ORM and is currently configured to connect to a MySQL database.

## Project Structure

- app.py: Streamlit app entrypoint, UI flow, ORM models, and persistence logic.
- README.md: setup and usage guide.

## Requirements

- Python 3.9+
- pip
- MySQL server (for full data persistence mode)

Python packages used by app.py:

- streamlit
- sqlalchemy
- mysql-connector-python

## Quick Start

1. Create and activate a virtual environment.

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies.

```bash
pip install streamlit sqlalchemy mysql-connector-python
```

3. Run the app.

```bash
streamlit run app.py
```

4. Open browser:

- http://localhost:8501

## Database Configuration

The app currently uses a hardcoded MySQL URL in app.py.

Current behavior:

- SQLAlchemy engine is created at startup.
- ORM tables are auto-created with Base.metadata.create_all(bind=engine).
- Some migration-like logic is applied at runtime for participant_attitudes after-columns.

Important notes:

- Ensure your MySQL service is running and the target database exists.
- Ensure credentials, host, and port in app.py match your local environment.
- If DB is unavailable, parts of the app can still render with fallback/mock task content, but write operations that require DB will fail.

Recommended local practice:

- Move DB URL to environment variables (instead of hardcoded secrets).
- Example pattern:

```python
import os
DB_URL = os.getenv("HOPES_FEARS_DB_URL")
```

## Survey Flow (High Level)

The app is a multi-page workflow managed by st.session_state.page.

- Page 0: consent information.
- Page 1: participant entry (Prolific ID and role selection).
- Page 2-5: baseline profile and initial fear/hope responses.
- Page 6-7: task gallery and pairwise task choice interactions.
- Page 8: post-survey fear/hope responses.
- Page 9: completion step.

All key inputs are validated as mandatory before advancing.

## Data Captured

The app records data into multiple tables, including:

- participants
- participant_profile
- participant_attitudes
- participant_task_gallery_events
- participant_ai_scale
- participant_task_pair_choices
- occupations
- occupation_tasks
- task_pairs

## Troubleshooting

1. App does not start because of missing packages

- Re-run dependency install in your active virtual environment.

2. DB connection error on startup

- Verify MySQL server status.
- Verify DB URL, username, password, host, and port.
- Confirm target database and user permissions.

3. Blank or fallback task content

- Check that occupations, occupation_tasks, and task_pairs have active rows.
- The app falls back to internal mock data when DB task data is not available.

## Next Improvements

- Add a requirements.txt file for reproducible setup.
- Externalize all secrets/configuration to environment variables.
- Add structured migration tooling (for example Alembic) instead of runtime ALTER TABLE logic.
- Add tests for DB write paths and page-state transitions.