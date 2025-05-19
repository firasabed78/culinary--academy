from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class CurriculumMapping(Base):
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"))
    program_outcome = Column(String)  # Or Integer, depending on the data

    course = relationship("Course", back_populates="curriculum_mappings")
