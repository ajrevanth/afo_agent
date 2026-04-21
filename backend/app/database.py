from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from helpers.schema import Base  # single source of truth for all tables
from app.settings import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
