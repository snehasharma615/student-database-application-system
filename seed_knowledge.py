from vector_store import add_knowledge, collection_count

documents = [
    "Student Database Application System manages structured student records such as name, email, age, gender, course, semester, GPA and city.",
    "The system uses FastAPI to expose RESTful APIs and automatically provides interactive Swagger documentation at /docs.",
    "SQLite is used for structured student records. SQLAlchemy provides ORM-based database access and CRUD operations.",
    "Gemini is used for natural-language understanding and response generation in the AI chatbot.",
    "LangGraph orchestrates the chatbot workflow as separate nodes for intent classification, SQL retrieval, vector retrieval and answer generation.",
    "ChromaDB is the selected vector database for semantic retrieval of unstructured student-management knowledge.",
    "The project keeps secrets in a .env file. API keys should never be hardcoded in Python source files.",
    "CRUD means Create, Read, Update and Delete. These operations form the main student database API.",
    "B.Tech CSE refers to the Computer Science and Engineering course used in the sample student data. The database stores the course as a structured field.",
    "The student database uses a GPA scale from 0 to 10. GPA is stored as a floating-point value and is used for statistics and chatbot queries.",
    "Student records can contain the genders Male, Female, Other, or Not specified. Statistics count Male and Female records separately.",
    "Swagger UI is available at /docs and ReDoc is available at /redoc when the FastAPI application is running.",
    "The chatbot routes database questions to SQL retrieval and knowledge questions to ChromaDB retrieval using a LangGraph conditional edge.",
    "The application uses SQLite for transactional structured records and ChromaDB for semantic retrieval. They serve different purposes.",
]
ids=[f"knowledge-{i}" for i in range(len(documents))]
metadatas=[{"source":"project_knowledge","type":"capstone"} for _ in documents]
add_knowledge(documents, ids, metadatas)
print(f"Knowledge base ready. Documents in ChromaDB: {collection_count()}")
