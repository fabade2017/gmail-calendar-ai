import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sqlite_path = os.getenv("SQLITE_PATH", "./gmail_calendar_ai.db")
    DATABASE_URL = f"sqlite:///{sqlite_path}"

if DATABASE_URL.startswith("mysql"):
    engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, future=True, connect_args={"check_same_thread": False})

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def init_db():
    from models import Base

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
