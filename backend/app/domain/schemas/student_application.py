from typing import Optional
from datetime import date

from pydantic import BaseModel


# Shared properties
class StudentApplicationBase(BaseModel):
    applicant_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


# Properties to receive on item creation
class StudentApplicationCreate(StudentApplicationBase):
    applicant_name: str
    date_of_birth: date
    email: str


# Properties to receive on item update
class StudentApplicationUpdate(StudentApplicationBase):
    pass


# Properties shared by models stored in DB
class StudentApplicationInDBBase(StudentApplicationBase):
    id: int

    class Config:
        orm_mode = True


# Properties to return to client
class StudentApplication(StudentApplicationInDBBase):
    pass


# Properties properties stored in DB
class StudentApplicationInDB(StudentApplicationInDBBase):
    pass
