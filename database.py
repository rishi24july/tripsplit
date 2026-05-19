import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Local pe SQLite, Render pe PostgreSQL automatically use hoga
db_url = os.environ.get("DATABASE_URL", "sqlite:///./tripsplit.db")

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
