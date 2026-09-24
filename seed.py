from database import Base, SessionLocal, engine
from models import Student

Base.metadata.create_all(bind=engine)

DATA = [
("Aarav Sharma","aarav@example.com",21,"Male","B.Tech CSE",6,8.7,"Dehradun"),
("Ananya Singh","ananya@example.com",20,"Female","B.Tech CSE",4,9.1,"Rishikesh"),
("Rohan Verma","rohan@example.com",22,"Male","B.Tech ECE",8,7.6,"Haridwar"),
("Priya Joshi","priya@example.com",21,"Female","B.Tech CSE",6,8.9,"New Tehri"),
("Kabir Rawat","kabir@example.com",20,"Male","B.Tech IT",4,7.9,"Pauri"),
("Meera Negi","meera@example.com",22,"Female","B.Tech CSE",8,9.3,"Srinagar"),
("Arjun Bisht","arjun@example.com",21,"Male","B.Tech ME",6,7.2,"Tehri"),
("Ishita Kapoor","ishita@example.com",20,"Female","B.Tech ECE",4,8.4,"Dehradun"),
("Dev Thapliyal","dev@example.com",23,"Male","B.Tech CSE",8,8.1,"Kotdwar"),
("Simran Kandari","simran@example.com",21,"Female","B.Tech IT",6,9.0,"Mussoorie"),
]

db = SessionLocal()
try:
    existing = {x[0] for x in db.query(Student.email).all()}
    added = 0
    for row in DATA:
        if row[1] in existing:
            continue
        db.add(Student(full_name=row[0], email=row[1], age=row[2], gender=row[3],
                       course=row[4], semester=row[5], gpa=row[6], city=row[7]))
        added += 1
    db.commit()
    print(f"Seed complete. Added {added} students.")
finally:
    db.close()
