from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Transcript(Base):
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("user.id"))
    gpa = Column(String)  # Or Float, depending on the precision needed
    courses = relationship("Grading", back_populates="transcript")
    student = relationship("User", back_populates="transcripts")
