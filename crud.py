from sqlalchemy import func, select
from sqlalchemy.orm import Session
from models import Student

def create_student(db, student):
    record = Student(**student.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_students(db, skip=0, limit=100, search=None):
    stmt = select(Student).order_by(Student.id.desc()).offset(skip).limit(limit)
    if search:
        p = f"%{search.strip()}%"
        stmt = (
            select(Student)
            .where(
                Student.full_name.ilike(p)
                | Student.email.ilike(p)
                | Student.course.ilike(p)
            )
            .order_by(Student.id.desc())
            .offset(skip)
            .limit(limit)
        )
    return list(db.scalars(stmt).all())

def get_student(db, student_id):
    return db.get(Student, student_id)

def update_student(db, student_id, data):
    record = db.get(Student, student_id)
    if not record:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record

def delete_student(db, student_id):
    record = db.get(Student, student_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True

def get_stats(db):
    total = db.scalar(select(func.count(Student.id))) or 0
    avg = db.scalar(select(func.avg(Student.gpa))) or 0
    male = db.scalar(select(func.count(Student.id)).where(func.lower(Student.gender) == "male")) or 0
    female = db.scalar(select(func.count(Student.id)).where(func.lower(Student.gender) == "female")) or 0
    return {
        "total_students": int(total),
        "average_gpa": round(float(avg), 2),
        "male_students": int(male),
        "female_students": int(female),
        "other_students": max(int(total) - int(male) - int(female), 0),
    }
