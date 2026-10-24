# Job Mitra — Apna Career Mitra

A Flask-based, server-rendered job portal concept for fresh graduates and IT job seekers. It includes candidate, recruiter, and administrator workflows for job discovery, applications, moderation, and matching.

## Static GitHub Pages preview

This repository uses Jinja templates and Flask routes, so the complete application cannot run on GitHub Pages. The static preview is an informational landing page only; job search, login, applications, recruiter tools, moderation, and database operations require the Flask backend.

## Project information

- **Application:** Python + Flask + Jinja2
- **UI:** HTML, CSS, JavaScript
- **Database:** SQLite by default; optional MySQL configuration
- **Application source:** `app.py`, `routes/`, `templates/`, `static/`
- **Tests:** `tests/` and `scripts/smoke_test.py`

## Full local run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`. Replace the example secret with a strong local secret in `.env`; never commit real credentials. Run tests using `python -m pytest tests/ -v`.

## Hosting

For the full service, deploy the Flask application on a Python-capable host, configure a persistent database and secret environment variables, disable debug mode, enable HTTPS, and verify key user flows. GitHub Pages does not execute Flask or persist application data.
