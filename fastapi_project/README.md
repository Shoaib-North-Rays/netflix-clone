# Standalone FastAPI project

This small API lives in its own folder and does not replace or modify the Django project.

## Run

From the repository root:

```bash
python -m pip install -r fastapi_project/requirements.txt
python -m uvicorn main:app --app-dir fastapi_project --reload
```

Then open `http://127.0.0.1:8000/` or the interactive API docs at `http://127.0.0.1:8000/docs`.

Endpoints:
- `GET /` — welcome response
- `GET /health` — health status
