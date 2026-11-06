# Standalone FastAPI Movie API

This is a separate FastAPI application in the repository root. It does not import or run the existing Django project. The existing Django files are left untouched.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements-fastapi.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` for the service summary and `http://127.0.0.1:8000/docs` for interactive API documentation. Health check: `http://127.0.0.1:8000/health`.

SQLite data is stored in `fastapi.db` by default (ignored by Git). Set `FASTAPI_DATABASE` to use a different database file path.

## API

- `GET /api/v1/movies?q=search&limit=20&offset=0` — list/search movies
- `POST /api/v1/movies` — create a movie
- `GET /api/v1/movies/{movie_id}` — retrieve one
- `PATCH /api/v1/movies/{movie_id}` — update supplied fields
- `DELETE /api/v1/movies/{movie_id}` — delete one

Example create request:

```json
{
  "title": "Arrival",
  "description": "A linguist works to communicate with visitors.",
  "release_year": 2016,
  "duration_minutes": 116
}
```

The new API starts with an empty database; it does not automatically migrate Django data.
