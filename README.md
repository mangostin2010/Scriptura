# Scriptura

Be closer to God through structured daily Bible reading, deep reflection, prayer, and elegant digital tools designed to encourage genuine faith and daily gratitude.

Scriptura is a Flask web application for a daily spiritual discipline: read Scripture, memorize and apply a verse, record prayer requests, and keep a gratitude journal -- all tracked per day against your account.

## Features

- **Daily Scripture reading** -- a chapter of Proverbs keyed to the day of the month, with completion tracking.
- **Verse memorization & application** -- record a self-rated accuracy score and how you will apply the verse of the day.
- **Prayer requests** -- save up to three prayer topics per day.
- **Gratitude journal** -- capture five things you are thankful for each day.
- **History** -- review all of your past daily records.
- **Bible reader** -- browse the full KJV by book and chapter.
- **Full-text search** -- search across the entire KJV (capped at 200 results).
- **Accounts** -- register, log in, and log out with hashed passwords.
- **Background prayer music** -- an optional looping audio player with volume control that persists playback across pages.

## Tech stack

- Python / Flask
- Flask-SQLAlchemy with SQLite (`scriptura.db`)
- Jinja2 templates styled with Tailwind CSS (CDN) and custom Google Fonts
- KJV text loaded from `en_kjv.json`

## Getting started

### Prerequisites

- Python 3.x
- `en_kjv.json` in the project root (the KJV Bible data the app reads at startup)

### Install

```bash
pip install flask flask-sqlalchemy
```

### Run

```bash
python app.py
```

The app starts on `http://0.0.0.0:5000`. The SQLite database (`scriptura.db`) is created automatically on first run.

## Project structure

```
app.py            Flask app: routes, models, KJV loading
view_db.py        Read-only CLI inspector for scriptura.db
en_kjv.json       KJV Bible data
templates/        Jinja2 templates
static/           CSS, JS, and background audio
scriptura.db      SQLite database (auto-generated)
```

## Inspecting the database

```bash
python view_db.py
```

Prints the contents of every table; password hashes are masked.

## Data model

- **User** -- `username`, `email` (unique), `password_hash`.
- **DailyRecord** -- one row per user per day (`YYYY-MM-DD`), holding reading completion, verse accuracy/application, three prayer fields, and five gratitude fields.

## Notes

- `app.secret_key` is hard-coded for development. Set a secure secret before deploying.
- `debug=True` is enabled in `app.py`; disable it for production.
