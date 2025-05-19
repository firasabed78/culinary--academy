from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Grading(Base):
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("user.id"))
    course_id = Column(Integer, ForeignKey("course.id"))
    grade = Column(String)  # e.g., "A+", "B", "C-"

    student = relationship("User", back_populates="gradings")
    course = relationship("Course", back_populates="gradings")
