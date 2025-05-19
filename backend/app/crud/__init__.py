"""
CRUD module initialization for the Culinary Academy Student Registration system.
This file exports CRUD operation instances for all system entities.
"""

from app.crud.crud_user import CRUDUser
from app.crud.crud_course import CRUDCourse
from app.crud.crud_enrollment import CRUDEnrollment
from app.crud.crud_schedule import CRUDSchedule
from app.crud.crud_payment import CRUDPayment

from app.domain.models.user import User
from app.domain.models.course import Course
from app.domain.models.enrollment import Enrollment
from app.domain.models.schedule import Schedule
from app.domain.models.payment import Payment

# Create instances for direct import
user = CRUDUser(User)
course = CRUDCourse(Course)
enrollment = CRUDEnrollment(Enrollment)
schedule = CRUDSchedule(Schedule)
payment = CRUDPayment(Payment)