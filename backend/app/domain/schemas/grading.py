from typing import Optional

from pydantic import BaseModel


# Shared properties
class GradingBase(BaseModel):
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    grade: Optional[str] = None


# Properties to receive on item creation
class GradingCreate(GradingBase):
    student_id: int
    course_id: int
    grade: str


# Properties to receive on item update
class GradingUpdate(GradingBase):
    pass


# Properties shared by models stored in DB
class GradingInDBBase(GradingBase):
    id: int
    student_id: int
    course_id: int
    grade: str

    class Config:
        orm_mode = True


# Properties to return to client
class Grading(GradingInDBBase):
    pass


# Properties properties stored in DB
class GradingInDB(GradingInDBBase):
    pass
