# Student Database Application System – Backend

AI & ML Internship Final Project

A modular Student Database Application System built with **FastAPI, SQLite, SQLAlchemy, Gemini, LangGraph and ChromaDB**.

## Internship requirements covered

- Modular backend architecture
- FastAPI REST APIs
- CRUD operations
- Swagger/OpenAPI documentation
- Deployable backend service configuration
- Gemini API integration
- AI chatbot using LangGraph
- Student database interaction through natural language
- Vector database research and implementation
- GitHub-ready project structure
- `.env` based secret management

## Architecture

```text
Client / Browser
      |
      v
   FastAPI
      |
      +----------------------+
      |                      |
      v                      v
 Student CRUD             /chat
      |                      |
      v                      v
   SQLite                LangGraph
                             |
               +-------------+-------------+
               |             |             |
          classify       SQL query     vector retrieve
               |             |             |
               |             v             v
               |          SQLite       ChromaDB
               |             \             /
               +---------------> answer
                                  |
                                  v
                               Gemini
                                  |
                                  v
                           Natural-language response
```

## Why two databases?

**SQLite** is the system of record for structured student information.

**ChromaDB** is the vector database for semantic retrieval from student-related knowledge documents. It is useful for questions where exact relational filtering is not enough, such as searching project notes and course-related knowledge stored in the local knowledge collection.

The project uses Chroma's persistent local client so the vector store is saved on disk during local development.

## Project structure

```text
student_ai_management_system_final/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── render.yaml
├── database.py
├── models.py
├── schemas.py
├── crud.py
├── chatbot_graph.py
├── vector_store.py
├── main.py
├── seed.py
├── seed_knowledge.py
├── vector_db_research.md
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── tests/
    └── test_api.py
```

## Requirements

- Python 3.10 or newer
- Gemini API key for live chatbot generation
- Internet access on first ChromaDB embedding-model initialization

## Windows setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Put your Gemini API key in `.env`.

Then:

```powershell
python seed.py
python seed_knowledge.py
uvicorn main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health: http://127.0.0.1:8000/health

## Chatbot examples

Try:

```text
How many students are there?
What is the average GPA?
How many female students are there?
Show students with GPA above 8.5.
Who are the top 3 students by GPA?
Tell me about the CSE course.
What is the purpose of this student management system?
```

The first group is primarily handled through SQLite SQL retrieval; knowledge-oriented questions can use ChromaDB retrieval. LangGraph orchestrates the workflow.

## Tests

Run the isolated test suite with:

```powershell
python -m pytest -q
```

Tests use an in-memory SQLite database and do not delete the local `students.db`.

## GitHub

Do not commit `.env`, `students.db`, or `chroma_db/`.

```powershell
git init
git add .
git commit -m "Build Student AI Management System"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Deployment

`render.yaml` is included as a deploy configuration. Set `GEMINI_API_KEY` as a secret/environment variable in the deployment platform.

For production, use a managed relational database and managed/server-backed vector database rather than relying on local SQLite/Chroma persistence. The local versions are intentionally simple for the internship capstone.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/students` | Create student |
| GET | `/students` | List/search students |
| GET | `/students/{id}` | Get one student |
| PUT | `/students/{id}` | Update student |
| DELETE | `/students/{id}` | Delete student |
| GET | `/stats` | Student statistics |
| POST | `/chat` | LangGraph + Gemini chatbot |

Swagger automatically documents and lets you test all endpoints at `/docs`.


## Internship hardening updates

The submission version includes:
- safer SELECT-only chatbot SQL validation, including trailing semicolon normalization, comment blocking, UNION/system-table blocking, and a 100-row limit;
- graceful Gemini failure handling and JSON-fence parsing;
- isolated in-memory API tests with mocked Gemini chatbot tests;
- explicit validation for non-null student update fields and controlled gender values;
- safer dashboard event handling without inline JSON `onclick`;
- Render seeding for SQLite/ChromaDB and `/health` health checks;
- expanded vector-database research and project knowledge documents.
