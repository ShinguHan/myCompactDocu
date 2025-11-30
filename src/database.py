from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# For local development, we'll use SQLite for simplicity if Postgres isn't ready,
# but the goal is Postgres.
# DB_URL = "postgresql://user:password@localhost/dbname"
# Using SQLite for now to ensure immediate runnability without external deps setup
DB_URL = "sqlite:///./cute_docu_shelf.db"

engine = create_engine(
    DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
