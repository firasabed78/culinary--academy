# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base
from app.domain.models.user import User
from app.domain.models.course import Course
from app.domain.models.enrollment import Enrollment
from app.domain.models.payment import Payment
from app.domain.models.schedule import Schedule
from app.domain.models.document import Document
from app.domain.models.notification import Notification