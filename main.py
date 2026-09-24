from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud
from chatbot_graph import ask_chatbot
from database import Base, engine, get_db
from schemas import ChatRequest, ChatResponse, StatsResponse, StudentCreate, StudentRead, StudentUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Database Application System",
    description="FastAPI + SQLite + Gemini + LangGraph + ChromaDB",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "student-database-application-system"}

@app.post("/students", response_model=StudentRead, status_code=201)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_student(db, student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A student with this email already exists.")

@app.get("/students", response_model=list[StudentRead])
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    return crud.get_students(db, skip, limit, search)

@app.get("/students/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(404, "Student not found.")
    return student

@app.put("/students/{student_id}", response_model=StudentRead)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    try:
        student = crud.update_student(db, student_id, data)
    except IntegrityError as exc:
        db.rollback()
        if "email" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(409, "A student with this email already exists.")
        raise HTTPException(422, "The student data violates a database constraint.")
    if not student:
        raise HTTPException(404, "Student not found.")
    return student

@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise HTTPException(404, "Student not found.")

@app.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    return ChatResponse(
        question=request.question,
        **ask_chatbot(db, request.question),
    )
