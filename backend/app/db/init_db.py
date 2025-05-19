


"""
init_db.py - Database initialization script
This file handles the initialization of the database for the Culinary Academy
Student Registration system, including creating initial admin users, sample
courses, and ensuring database tables are properly set up.
"""

import logging
from sqlalchemy.orm import Session # The Session is used to interact with the database, allowing you to perform queries and manage database transactions.
from datetime import date, timedelta # Date for noraml date and time, timedelta for for performing date arithmetic (like adding days to a date)

from app.db.session import SessionLocal # This imports a custom database session factory that's configured for the application. It's used to create new database sessions.
from app.core.config import settings #  This imports the application's configuration settings, which contain important values like: Admin user credentials
#Database connection details
#Other application-wide settings
from app.core.security import get_password_hash # hashing function to securely store passwords
from app.domain.models.user import User, UserRole #  The UserRole enum that defines different user roles (like ADMIN, INSTRUCTOR)model class that defines the structure of user data in the database 
from app.domain.models.course import Course # The Course model that defines the structure of course data in the database


logger = logging.getLogger(__name__)

def init_db() -> None:
    """
    Initialize database with required initial data for the Culinary Academy.
    
    This function runs when the application starts, ensuring the database
    has necessary seed data for proper operation.
    """
    db = SessionLocal()
    try:
        # Create tables if they don't exist
        # Note: For production, use Alembic migrations instead
        # Base.metadata.create_all(bind=engine)
        
        # Create admin user if it doesn't exist
        create_initial_users(db)
        
        # Create initial culinary courses if needed
        create_initial_courses(db)
    finally:
        db.close()


def create_initial_users(db: Session) -> None:
    """
    Create initial admin and chef instructor users if they don't exist.
    
    Parameters
    ----------
    db: SQLAlchemy session
    """
    # Check if admin user exists
    admin = db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL).first()
    if not admin:
        logger.info("Creating initial admin user")
        admin_user = User(
            email=settings.FIRST_ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
            full_name="Culinary Academy Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info(f"Admin user created: {admin_user.email}")
    else:
        logger.info("Admin user already exists")
        
    # Create head chef instructor if needed
    head_chef_email = getattr(settings, 'HEAD_CHEF_EMAIL', 'headchef@culinaryacademy.com')
    head_chef_password = getattr(settings, 'HEAD_CHEF_PASSWORD', 'password123')
    
    head_chef = db.query(User).filter(User.email == head_chef_email).first()
    if not head_chef:
        logger.info("Creating head chef instructor")
        chef_user = User(
            email=head_chef_email,
            hashed_password=get_password_hash(head_chef_password),
            full_name="Head Chef Instructor",
            role=UserRole.INSTRUCTOR,
            is_active=True
        )
        db.add(chef_user)
        db.commit()
        db.refresh(chef_user)
        logger.info(f"Head chef instructor created: {chef_user.email}")


def create_initial_courses(db: Session) -> None:
    """
    Create initial culinary courses if they don't exist.
    
    Parameters
    ----------
    db: SQLAlchemy session
    """
    # Check if any courses exist
    course_count = db.query(Course).count()
    if course_count == 0:
        logger.info("Creating initial culinary courses")
        
        # Find instructor for courses
        instructor = db.query(User).filter(User.role == UserRole.INSTRUCTOR).first()
        instructor_id = instructor.id if instructor else None
        
        # Calculate dates - start courses in the near future
        today = date.today()
        
        # Create foundational courses
        foundational_courses = [
            {
                "title": "Culinary Foundations I: Basic Techniques",
                "description": "Introduction to fundamental cooking techniques, knife skills, and kitchen safety. Students will learn the building blocks of culinary arts through hands-on preparation of classic recipes.",
                "instructor_id": instructor_id,
                "duration": 30,  # 30 days
                "price": 1200.00,
                "capacity": 20,
                "start_date": today + timedelta(days=30),
                "end_date": today + timedelta(days=60),
                "is_active": True,
                "image_url": "/uploads/courses/culinary-foundations.jpg"
            },
            {
                "title": "Baking and Pastry Essentials",
                "description": "Fundamentals of baking including breads, pastries, and desserts. Learn proper measuring techniques, ingredient functions, and the science behind baking.",
                "instructor_id": instructor_id,
                "duration": 25,  # 25 days
                "price": 1100.00,
                "capacity": 16,
                "start_date": today + timedelta(days=45),
                "end_date": today + timedelta(days=70),
                "is_active": True,
                "image_url": "/uploads/courses/baking-pastry.jpg"
            },
            {
                "title": "International Cuisines",
                "description": "Exploration of culinary traditions from around the world. Each week focuses on a different region, including techniques, ingredients, and cultural significance of dishes.",
                "instructor_id": instructor_id,
                "duration": 40,  # 40 days
                "price": 1500.00,
                "capacity": 18,
                "start_date": today + timedelta(days=60),
                "end_date": today + timedelta(days=100),
                "is_active": True,
                "image_url": "/uploads/courses/international-cuisines.jpg"
            },
            {
                "title": "Farm to Table Cooking",
                "description": "Learn to source and prepare seasonal ingredients with an emphasis on sustainability, local produce, and flavor maximization. Includes field trips to local farms and markets.",
                "instructor_id": instructor_id,
                "duration": 35,  # 35 days
                "price": 1350.00,
                "capacity": 15,
                "start_date": today + timedelta(days=75),
                "end_date": today + timedelta(days=110),
                "is_active": True,
                "image_url": "/uploads/courses/farm-to-table.jpg"
            },
            {
                "title": "Professional Kitchen Management",
                "description": "Advanced course covering kitchen organization, staff management, menu planning, cost control, and food safety regulations for aspiring chef managers.",
                "instructor_id": instructor_id,
                "duration": 45,  # 45 days
                "price": 1800.00,
                "capacity": 12,
                "start_date": today + timedelta(days=90),
                "end_date": today + timedelta(days=135),
                "is_active": True,
                "image_url": "/uploads/courses/kitchen-management.jpg"
            }
        ]
        
        for course_data in foundational_courses:
            course = Course(**course_data)
            db.add(course)
        
        db.commit()
        logger.info(f"Created {len(foundational_courses)} initial culinary courses")