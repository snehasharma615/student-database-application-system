import json
import os
import re
from typing import TypedDict
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, START, END
from sqlalchemy import text
from vector_store import search_knowledge

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|REPLACE|VACUUM|TRUNCATE|GRANT|REVOKE|UNION|INTERSECT|EXCEPT)\b",
    re.I,
)

class ChatState(TypedDict, total=False):
    question: str
    intent: str
    sql: str
    rows: list[dict]
    documents: list[str]
    answer: str
    error: str
    db: object

def get_client():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return genai.Client(api_key=key) if key else None

def generate(prompt, temperature=0.1, max_tokens=500):
    client = get_client()
    if not client:
        return None
    try:
        result = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return (result.text or "").strip()
    except Exception:
        return None

def classify_intent(state: ChatState):
    q = state["question"]
    client = get_client()
    keywords = [
        "student", "gpa", "grade", "semester", "course", "male", "female",
        "gender", "average", "count", "how many", "show", "find", "list",
        "highest", "lowest", "above", "below", "city"
    ]
    fallback = "database" if any(k in q.lower() for k in keywords) else "knowledge"

    if not client:
        return {"intent": fallback}

    prompt = f"""
Classify this student-management question into exactly one label:
DATABASE = asks about actual student records, counts, GPA, names, courses, semesters, genders, cities, etc.
KNOWLEDGE = asks about the application, concepts, architecture, FastAPI, LangGraph, ChromaDB, Gemini, CRUD, or project documentation.
Return JSON only: {{"intent":"DATABASE"}} or {{"intent":"KNOWLEDGE"}}.
Question: {q}
"""
    raw = generate(prompt, temperature=0, max_tokens=100) or ""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        intent = json.loads(cleaned).get("intent", "KNOWLEDGE").upper()
    except Exception:
        intent = fallback
    return {"intent": intent if intent in {"DATABASE", "KNOWLEDGE"} else fallback}

def build_sql(state: ChatState):
    """Build a safe SQL query for common student database questions."""
    
    question = state["question"].lower().strip()

    # Total number of students
    if "how many students" in question or "total students" in question:
        return {
            "sql": "SELECT COUNT(*) AS total_students FROM students"
        }

    # Female students
    if "female" in question and (
        "how many" in question
        or "count" in question
        or "number" in question
    ):
        return {
            "sql": "SELECT COUNT(*) AS female_students FROM students WHERE gender = 'Female'"
        }

    # Male students
    if "male" in question and (
        "how many" in question
        or "count" in question
        or "number" in question
    ):
        return {
            "sql": "SELECT COUNT(*) AS male_students FROM students WHERE gender = 'Male'"
        }

    # Average GPA
    if "average gpa" in question or "average grade" in question:
        return {
            "sql": "SELECT AVG(gpa) AS average_gpa FROM students"
        }

    # Highest GPA
    if (
        "highest gpa" in question
        or "top student" in question
        or "best student" in question
    ):
        return {
            "sql": (
                "SELECT id, full_name, email, age, gender, course, "
                "semester, gpa FROM students ORDER BY gpa DESC LIMIT 1"
            )
        }

    # Lowest GPA
    if "lowest gpa" in question:
        return {
            "sql": (
                "SELECT id, full_name, email, age, gender, course, "
                "semester, gpa FROM students ORDER BY gpa ASC LIMIT 1"
            )
        }

    # List all students
    if (
        "list all students" in question
        or "show all students" in question
        or "show students" in question
        or "list students" in question
    ):
        return {
            "sql": (
                "SELECT id, full_name, email, age, gender, course, "
                "semester, gpa FROM students LIMIT 100"
            )
        }

    # For other database questions, use Gemini
    client = get_client()

    if not client:
        return {
            "error": "Gemini is not configured. Add GEMINI_API_KEY to .env."
        }

    prompt = f"""
Convert the following question into ONE safe SQLite SELECT query.

Table: students

Columns:
id, full_name, email, age, gender, course, semester, gpa

Rules:
- Return SQL only.
- SELECT statements only.
- Use only the students table.
- No INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or other write/DDL statements.
- No multiple SQL statements.
- Add LIMIT 100 for list queries when needed.
- The gender column contains exactly 'Male' and 'Female'.
- For female students, use gender = 'Female'.
- For male students, use gender = 'Male'.

Question: {state["question"]}
"""

    raw = generate(prompt, temperature=0, max_tokens=250) or ""
    raw = raw.strip()

    match = re.search(r"\bSELECT\b.*", raw, flags=re.I | re.S)

    if not match:
        return {
            "error": "Gemini did not return a SQL SELECT query."
        }

    sql = match.group(0).strip()

    return {"sql": sql}

def execute_sql(state: ChatState):
    if state.get("error"):
        return {}
    try:
        rows = [dict(r) for r in state["db"].execute(text(state["sql"])).mappings().all()]
        return {"rows": rows}
    except Exception:
        return {"error": "The generated database query could not be executed safely."}

def retrieve_knowledge(state: ChatState):
    try:
        return {"documents": search_knowledge(state["question"], n_results=3)}
    except Exception:
        return {"documents": [], "error": "The knowledge base could not be queried."}

def route_after_classify(state: ChatState):
    intent = str(state.get("intent", "")).strip().upper()
    return "database" if intent == "DATABASE" else "knowledge"

def generate_answer(state: ChatState):
    if state.get("error"):
        return {"answer": state["error"]}

    if str(state.get("intent", "")).strip().upper() == "DATABASE":
        rows = state.get("rows", [])

        if not rows:
            return {
                "answer": "No matching records were found in the student database."
            }

        context = json.dumps(rows, default=str)

        prompt = f"""
Answer the user's question using ONLY this student database result.

Do not invent facts.

Question: {state["question"]}

Database result:
{context}

Be concise and clear.
"""

        answer = generate(
            prompt,
            temperature=0.2,
            max_tokens=500
        )

        if answer and not answer.startswith("Gemini is unavailable"):
            return {"answer": answer.strip()}

        first_row = rows[0]

        if isinstance(first_row, dict) and len(first_row) == 1:
            key, value = next(iter(first_row.items()))

            if "female" in key.lower():
                return {
                    "answer": f"There are {value} female students in the database."
                }

            if "male" in key.lower():
                return {
                    "answer": f"There are {value} male students in the database."
                }

            if "total" in key.lower():
                return {
                    "answer": f"There are {value} students in the database."
                }

            if "average" in key.lower():
                return {
                    "answer": f"The average GPA is {value}."
                }

        return {
            "answer": f"Database result: {context}"
        }

    else:
        docs = "\n\n".join(state.get("documents", []))

        prompt = f"""
Answer the user's question using the provided project knowledge.

If the knowledge does not contain the answer, say that the information
is not available in the provided project knowledge.

Question:
{state["question"]}

Knowledge:
{docs}
"""

        answer = generate(
            prompt,
            temperature=0.2,
            max_tokens=500
        )

        return {
            "answer": answer or "Gemini is unavailable right now."
        }
def build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("classify", classify_intent)
    graph.add_node("build_sql", build_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("retrieve_knowledge", retrieve_knowledge)
    graph.add_node("generate_answer", generate_answer)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route_after_classify, {"database": "build_sql", "knowledge": "retrieve_knowledge"})
    graph.add_edge("build_sql", "execute_sql")
    graph.add_edge("execute_sql", "generate_answer")
    graph.add_edge("retrieve_knowledge", "generate_answer")
    graph.add_edge("generate_answer", END)
    return graph.compile()

GRAPH = build_graph()

def ask_chatbot(db, question):
    result = GRAPH.invoke({"question": question, "db": db})
    return {
        "intent": result.get("intent", "KNOWLEDGE"),
        "sql": result.get("sql"),
        "retrieved_documents": result.get("documents", []),
        "answer": result.get("answer", "No answer generated."),
    }
