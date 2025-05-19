from typing import Optional

from pydantic import BaseModel


# Shared properties
class CurriculumMappingBase(BaseModel):
    course_id: Optional[int] = None
    program_outcome: Optional[str] = None


# Properties to receive on item creation
class CurriculumMappingCreate(CurriculumMappingBase):
    course_id: int
    program_outcome: str


# Properties to receive on item update
class CurriculumMappingUpdate(CurriculumMappingBase):
    pass


# Properties shared by models stored in DB
class CurriculumMappingInDBBase(CurriculumMappingBase):
    id: int
    course_id: int
    program_outcome: str

    class Config:
        orm_mode = True


# Properties to return to client
class CurriculumMapping(CurriculumMappingInDBBase):
    pass


# Properties properties stored in DB
class CurriculumMappingInDB(CurriculumMappingInDBBase):
    pass
