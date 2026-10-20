# AI Job Copilot

A simple job-search and application-tracking web app built with Python, FastAPI, Streamlit, and SQLite.

AI Job Copilot helps users discover job listings, save interesting opportunities, and keep track of their applications in one place.

## Features

- **Job discovery:** Fetch job listings from Arbeitnow.
- **Keyword search:** Search listings by role, technology, or skill.
- **Save jobs:** Choose which job listings to save to your collection.
- **Application tracking:** Track jobs as saved, applied, interview, rejected, or offer.
- **Application notes:** Keep notes about applications and interviews.
- **Job matching:** Score saved jobs using the project's job-scoring engine.
- **Dashboard:** View saved jobs, application statistics, and recommendations.
- **REST API:** Access functionality through FastAPI endpoints.
- **SQLite database:** Store saved jobs locally.

## Tech Stack

- Python
- FastAPI
- Streamlit
- SQLAlchemy
- SQLite
- Pydantic
- HTTPX
- Pytest

## Project Structure

```text
ai-job-copilot/
├── app/
│   ├── main.py
│   ├── dashboard.py
│   ├── models.py
│   ├── config.py
│   ├── database.py
│   ├── db_models.py
│   ├── init_db.py
│   ├── job_sources.py
│   ├── job_scoring.py
│   ├── migrate_db.py
│   └── test_db.py
├── tests/
│   ├── test_api.py
│   ├── test_job_sources.py
│   └── test_job_scoring.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 or newer
- pip
- Internet connection for fetching external job listings

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd ai-job-copilot
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Running the Application

Start the FastAPI backend in the first terminal:

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

Start the Streamlit dashboard in a second terminal:

```bash
python -m streamlit run app/dashboard.py
```

Streamlit will display the local dashboard URL in the terminal, usually:

http://localhost:8501

## How to Use

1. Open the Streamlit dashboard.
2. Go to **Find jobs**.
3. Search for a job title or keyword.
4. Review the available listings.
5. Select **Save job** for an opportunity you want to keep.
6. Open **Applications** to update its status and add notes.
7. Use **Overview** to review your saved jobs and recommendations.

Searching for jobs does not automatically save them. Jobs are added to your collection when you explicitly save them.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/health` | Health check |
| GET | `/jobs` | List saved jobs |
| POST | `/jobs` | Save a job |
| GET | `/jobs/search?q=python` | Search saved jobs |
| GET | `/jobs/discover` | Discover external jobs without saving |
| GET | `/jobs/import` | Legacy endpoint that fetches and saves jobs |
| GET | `/jobs/import/scored` | Legacy endpoint that fetches, scores, and saves jobs |
| PATCH | `/jobs/{job_id}/status` | Update application status and notes |
| GET | `/dashboard` | Retrieve dashboard metrics and recommendations |

The legacy import endpoints automatically save fetched jobs. The dashboard uses `/jobs/discover` for discovery and `/jobs` to save jobs explicitly.

## Running Tests

Run the test suite from the project root:

```bash
python -m pytest -v
```

## Data and Privacy

Saved jobs are stored in a local SQLite database. The database file should generally remain local and should not be committed to a public repository if it contains personal information.

Job listings are retrieved from Arbeitnow. Availability and listing details may change over time.

## Future Improvements

- Resume-based job matching
- More job sources
- Improved relevance scoring
- Job application reminders
- Export application data
- Automated deployment

## License

No license has been specified yet. Add a license if you intend to distribute or allow others to reuse the project.
