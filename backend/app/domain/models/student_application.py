from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class StudentApplication(Base):
    id = Column(Integer, primary_key=True, index=True)
    applicant_name = Column(String, index=True)
    date_of_birth = Column(Date)
    email = Column(String, index=True)
    phone_number = Column(String)
    address = Column(String)
    # Add other relevant fields like educational background, etc.
