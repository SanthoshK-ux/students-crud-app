
import sqlite3
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field


def get_connection():
    connection = sqlite3.connect("students.db")
    connection.row_factory = sqlite3.Row
    return connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                course TEXT
            )
        """)
    yield


app = FastAPI(title="Students CRUD API", lifespan=lifespan)


class Student(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dob: date
    email: EmailStr
    phone: str | None = None
    course: str | None = None


@app.post("/students", status_code=201)
def create_student(student: Student):
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO students (name, dob, email, phone, course)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    student.name,
                    student.dob.isoformat(),
                    str(student.email),
                    student.phone,
                    student.course,
                ),
            )
            student_id = cursor.lastrowid
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            return dict(row)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Email already exists")


@app.get("/students")
def list_students():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM students ORDER BY student_id"
        ).fetchall()
        return [dict(row) for row in rows]


@app.get("/students/{student_id}")
def get_student(student_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return dict(row)


@app.put("/students/{student_id}")
def update_student(student_id: int, student: Student):
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """UPDATE students
                   SET name = ?, dob = ?, email = ?, phone = ?, course = ?
                   WHERE student_id = ?""",
                (
                    student.name,
                    student.dob.isoformat(),
                    str(student.email),
                    student.phone,
                    student.course,
                    student_id,
                ),
            )

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Student not found")

            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            return dict(row)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Email already exists")


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM students WHERE student_id = ?",
            (student_id,),
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")

    return {"message": "Student deleted successfully"}
