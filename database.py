import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

db_url = os.environ.get("DATABASE_URL", "sqlite:///./tripsplit.db")

if "postgresql" in db_url:
    # pg8000 use karo aur sslmode URL se hatao
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://")
    db_url = db_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    engine = create_engine(
        db_url,
        connect_args={"ssl_context": True}
    )
else:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()