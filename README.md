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

The app reads its database URL from Streamlit secrets or environment variables.

Current behavior:

- SQLAlchemy engine is created at startup.
- ORM tables are auto-created with Base.metadata.create_all(bind=engine).
- Some migration-like logic is applied at runtime for participant_attitudes after-columns.
- If no DB URL is provided, the app falls back to a local SQLite file: survey.db.

Important notes:

- For production or Streamlit deployment, provide a real external database URL.
- Ensure your MySQL service is running and the target database exists.
- Ensure credentials, host, and port in your secrets or environment variables are correct.
- Local SQLite fallback is suitable for demos and local development, not long-term survey data collection.

Recommended local practice:

- Put DB credentials in one of these places:

```toml
# .streamlit/secrets.toml
DB_URL = "mysql+mysqlconnector://USERNAME:PASSWORD@HOST:3306/DATABASE_NAME"
```

```python
import os
DB_URL = os.getenv("HOPES_FEARS_DB_URL")
```

## Deploy To Streamlit Community Cloud

1. Push the latest code to GitHub.

2. Confirm these files exist in the repo:

- app.py
- requirements.txt

3. Go to Streamlit Community Cloud:

- https://share.streamlit.io/

4. Create a new app and connect your GitHub repository.

5. Use these settings:

- Repository: your GitHub repo
- Branch: main
- Main file path: app.py

6. In App settings -> Secrets, add your production database URL, for example:

```toml
DB_URL = "mysql+mysqlconnector://USERNAME:PASSWORD@HOST:3306/DATABASE_NAME"
```

7. Deploy the app. Streamlit will install packages from requirements.txt and publish a URL like:

- https://your-app-name.streamlit.app/

## Deployment Notes

- If your MySQL database is only available on 127.0.0.1, Streamlit Cloud will not be able to reach it.
- For cloud deployment, you need a publicly reachable or otherwise network-accessible database service.
- If you only want to demo the UI, the SQLite fallback can run without external DB secrets, but data persistence will be limited.

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