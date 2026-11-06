"""Standalone FastAPI movie catalog API; the existing Django app is not used."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field


DATABASE_PATH = Path(os.getenv("FASTAPI_DATABASE", "fastapi.db"))


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                release_year INTEGER NOT NULL CHECK (release_year BETWEEN 1888 AND 2200),
                duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
                created_at TEXT NOT NULL
            )"""
        )


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    release_year: int = Field(ge=1888, le=2200)
    duration_minutes: int = Field(gt=0, le=1000)


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    release_year: int | None = Field(default=None, ge=1888, le=2200)
    duration_minutes: int | None = Field(default=None, gt=0, le=1000)


class Movie(MovieCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


app = FastAPI(
    title="Movie Catalog API",
    description="A standalone FastAPI service for managing a movie catalog.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


def row_to_movie(row: sqlite3.Row) -> Movie:
    return Movie(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        release_year=row["release_year"],
        duration_minutes=row["duration_minutes"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"name": "Movie Catalog API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/movies", response_model=list[Movie], tags=["movies"])
def list_movies(
    q: str | None = Query(default=None, max_length=200, description="Search title and description"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Movie]:
    sql = "SELECT * FROM movies"
    parameters: list[object] = []
    if q:
        sql += " WHERE title LIKE ? OR description LIKE ?"
        term = f"%{q}%"
        parameters.extend((term, term))
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    parameters.extend((limit, offset))
    with get_connection() as connection:
        rows = connection.execute(sql, parameters).fetchall()
    return [row_to_movie(row) for row in rows]


@app.post(
    "/api/v1/movies",
    response_model=Movie,
    status_code=status.HTTP_201_CREATED,
    tags=["movies"],
)
def create_movie(movie: MovieCreate) -> Movie:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO movies (title, description, release_year, duration_minutes, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (movie.title, movie.description, movie.release_year, movie.duration_minutes, created_at),
        )
        row = connection.execute("SELECT * FROM movies WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return row_to_movie(row)


@app.get("/api/v1/movies/{movie_id}", response_model=Movie, tags=["movies"])
def get_movie(movie_id: int) -> Movie:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return row_to_movie(row)


@app.patch("/api/v1/movies/{movie_id}", response_model=Movie, tags=["movies"])
def update_movie(movie_id: int, changes: MovieUpdate) -> Movie:
    values = changes.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided")
    if any(value is None for value in values.values()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fields cannot be null")

    assignments = ", ".join(f"{field} = ?" for field in values)
    parameters = [*values.values(), movie_id]
    with get_connection() as connection:
        cursor = connection.execute(f"UPDATE movies SET {assignments} WHERE id = ?", parameters)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
        row = connection.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    return row_to_movie(row)


@app.delete("/api/v1/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["movies"])
def delete_movie(movie_id: int) -> Response:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
