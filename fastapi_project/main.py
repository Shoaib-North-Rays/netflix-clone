"""A small standalone FastAPI project, separate from the existing Django app."""

from fastapi import FastAPI

app = FastAPI(title="Standalone API", version="1.0.0")


@app.get("/")
def root():
    return {"message": "Standalone FastAPI project is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
