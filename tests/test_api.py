import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
import chatbot_graph

TEST_ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)

@pytest.fixture(autouse=True)
def isolated_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def student_payload(**overrides):
    payload = {"full_name":"Test Student","email":"test@example.com","age":21,"gender":"Male",
               "course":"B.Tech CSE","semester":6,"gpa":8.5,"city":"New Tehri"}
    payload.update(overrides)
    return payload

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_create_and_read(client):
    r = client.post("/students", json=student_payload())
    assert r.status_code == 201
    sid = r.json()["id"]
    r = client.get(f"/students/{sid}")
    assert r.status_code == 200
    assert r.json()["full_name"] == "Test Student"

def test_update_and_delete(client):
    sid = client.post("/students", json=student_payload()).json()["id"]
    r = client.put(f"/students/{sid}", json={"gpa":9.2})
    assert r.status_code == 200
    assert r.json()["gpa"] == 9.2
    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404

def test_duplicate_email(client):
    client.post("/students", json=student_payload())
    r = client.post("/students", json=student_payload(full_name="Another"))
    assert r.status_code == 409

def test_not_found_and_validation(client):
    assert client.get("/students/999").status_code == 404
    assert client.post("/students", json=student_payload(age=10)).status_code == 422
    assert client.put("/students/999", json={"gpa":9}).status_code == 404

def test_explicit_null_update_is_rejected(client):
    sid = client.post("/students", json=student_payload()).json()["id"]
    assert client.put(f"/students/{sid}", json={"age":None}).status_code == 422

def test_stats(client):
    client.post("/students", json=student_payload())
    r = client.get("/stats")
    assert r.status_code == 200
    assert r.json()["total_students"] == 1

def test_chatbot_database_flow_with_mocked_gemini(client, monkeypatch):
    client.post("/students", json=student_payload())
    responses = iter(['{"intent":"DATABASE"}','SELECT COUNT(*) AS total_students FROM students;','There is 1 student in the database.'])
    monkeypatch.setattr(chatbot_graph, "generate", lambda *args, **kwargs: next(responses))
    r = client.post("/chat", json={"question":"How many students are there?"})
    assert r.status_code == 200
    assert r.json()["intent"] == "DATABASE"
    assert "There is 1 student" in r.json()["answer"]

def test_chatbot_classifier_json_fence(monkeypatch):
    monkeypatch.setattr(chatbot_graph, "generate", lambda *args, **kwargs: '```json\n{"intent":"KNOWLEDGE"}\n```')
    monkeypatch.setattr(chatbot_graph, "get_client", lambda: object())
    result = chatbot_graph.classify_intent({"question":"What is LangGraph?"})
    assert result["intent"] == "KNOWLEDGE"

def test_sql_guard_and_limit(monkeypatch):
    monkeypatch.setattr(chatbot_graph, "generate", lambda *args, **kwargs: "```sql\nSELECT * FROM students LIMIT 999999;\n```")
    monkeypatch.setattr(chatbot_graph, "get_client", lambda: object())
    result = chatbot_graph.build_sql({"question":"show students"})
    assert result["sql"].endswith("LIMIT 100")
    assert ";" not in result["sql"]
    monkeypatch.setattr(chatbot_graph, "generate", lambda *args, **kwargs: "SELECT * FROM students UNION SELECT name FROM sqlite_master")
    result = chatbot_graph.build_sql({"question":"show students"})
    assert "error" in result
