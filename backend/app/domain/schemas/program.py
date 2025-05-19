from typing import Optional

from pydantic import BaseModel


# Shared properties
class ProgramBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on item creation
class ProgramCreate(ProgramBase):
    name: str


# Properties to receive on item update
class ProgramUpdate(ProgramBase):
    pass


# Properties shared by models stored in DB
class ProgramInDBBase(ProgramBase):
    id: int
    name: str

    class Config:
        orm_mode = True


# Properties to return to client
class Program(ProgramInDBBase):
    pass


# Properties properties stored in DB
class ProgramInDB(ProgramInDBBase):
    pass
