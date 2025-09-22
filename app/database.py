import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use environment variable for production, fallback to local MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:W7301%40shiv%23@localhost:3306/note_app"
)

# Create engine with connection pooling for production
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    echo=False           # Set to True for debug logs
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Keep objects loaded after commit
)

Base = declarative_base()