from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Gender = Literal["Male", "Female", "Other", "Not specified"]

class StudentBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    age: int = Field(ge=16, le=100)
    gender: Gender = "Not specified"
    course: str = Field(min_length=2, max_length=120)
    semester: int = Field(ge=1, le=12)
    gpa: float = Field(ge=0, le=10)
    city: str = Field(default="", max_length=100)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    age: int | None = Field(default=None, ge=16, le=100)
    gender: Gender | None = None
    course: str | None = Field(default=None, min_length=2, max_length=120)
    semester: int | None = Field(default=None, ge=1, le=12)
    gpa: float | None = Field(default=None, ge=0, le=10)
    city: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def reject_explicit_nulls(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        return self

class StudentRead(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)

class ChatResponse(BaseModel):
    question: str
    intent: str
    sql: str | None = None
    retrieved_documents: list[str] = []
    answer: str

class StatsResponse(BaseModel):
    total_students: int
    average_gpa: float
    male_students: int
    female_students: int
    other_students: int
