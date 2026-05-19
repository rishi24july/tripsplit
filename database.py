import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

db_url = os.environ.get("DATABASE_URL", "sqlite:///./tripsplit.db")

# pg8000 driver use karo PostgreSQL ke liye
if "postgresql" in db_url and "pg8000" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://")

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()