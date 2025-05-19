from typing import Optional

from pydantic import BaseModel


# Shared properties
class TranscriptBase(BaseModel):
    student_id: Optional[int] = None
    gpa: Optional[str] = None


# Properties to receive on item creation
class TranscriptCreate(TranscriptBase):
    student_id: int
    gpa: str


# Properties to receive on item update
class TranscriptUpdate(TranscriptBase):
    pass


# Properties shared by models stored in DB
class TranscriptInDBBase(TranscriptBase):
    id: int
    student_id: int
    gpa: str

    class Config:
        orm_mode = True


# Properties to return to client
class Transcript(TranscriptInDBBase):
    pass


# Properties properties stored in DB
class TranscriptInDB(TranscriptInDBBase):
    pass
