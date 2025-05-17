"""
Objective: Configure Alembic for database migrations.
This file sets up the database connection and migration environment for Alembic,
allowing for automatic schema migrations based on SQLAlchemy models.

This Alembic configuration file is responsible for setting up the database migration environment:

Purpose: It connects your SQLAlchemy models to Alembic's migration system
Key Features:

Imports all your models via the Base class
Uses the same database connection as your main application
Supports both online migrations (applying directly to the database) and offline migrations (generating SQL scripts)
Configures logging for migration operations


Integration Points:

References your application settings for database connection
Uses your SQLAlchemy Base metadata to track model changes

This file ensures that when you make changes to your SQLAlchemy models, Alembic can automatically detect those changes and generate the appropriate migration scripts to update your database schema.

"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings  # Import application settings
from app.db.base import Base  # Import SQLAlchemy Base with all models

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers based on the configuration in the Alembic .ini file.
fileConfig(config.config_file_name)

# Set up the SQLAlchemy models metadata for 'autogenerate' support
# This allows Alembic to detect model changes and generate migrations automatically
target_metadata = Base.metadata

# Function to get the database URL from application settings
# This ensures that the same database connection is used for migrations and the application
def get_url():
    return settings.SQLALCHEMY_DATABASE_URI

# Function for running migrations in 'offline' mode
# Offline mode generates SQL scripts without actually executing them against the database
def run_migrations_offline():
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()  # Get the database URL
    context.configure(
        url=url,
        target_metadata=target_metadata,  # Use the SQLAlchemy models metadata
        literal_binds=True,  # Use literal SQL parameter binding
        dialect_opts={"paramstyle": "named"},  # Use named parameters in SQL
    )
    
    # Execute the migrations
    with context.begin_transaction():
        context.run_migrations()

# Function for running migrations in 'online' mode
# Online mode actually executes the migrations against the database
def run_migrations_online():
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get the Alembic configuration section
    configuration = config.get_section(config.config_ini_section)
    # Override the SQLAlchemy URL with the one from application settings
    configuration["sqlalchemy.url"] = get_url()
    
    # Create a SQLAlchemy engine for the migrations
    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    
    # Execute the migrations within a connection
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# Decide whether to run migrations in offline or online mode
# This is determined by the Alembic command line option
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()