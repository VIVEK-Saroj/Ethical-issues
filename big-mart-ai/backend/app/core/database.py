from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

connect_args = {}
kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    kwargs["pool_pre_ping"] = True
    kwargs["pool_size"] = 5
    kwargs["max_overflow"] = 10
    # Supabase requires SSL; add sslmode if not already in the URL
    if "sslmode" not in settings.DATABASE_URL:
        sep = "&" if "?" in settings.DATABASE_URL else "?"
        db_url = settings.DATABASE_URL + sep + "sslmode=require"
    else:
        db_url = settings.DATABASE_URL

final_url = db_url if not settings.DATABASE_URL.startswith("sqlite") else settings.DATABASE_URL
engine = create_engine(final_url, connect_args=connect_args, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
