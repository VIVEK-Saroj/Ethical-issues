from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# Render provides postgres:// but SQLAlchemy needs postgresql://
_raw_url = settings.DATABASE_URL
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
kwargs = {}
if _raw_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    kwargs["pool_pre_ping"] = True
    kwargs["pool_size"] = 5
    kwargs["max_overflow"] = 10

engine = create_engine(_raw_url, connect_args=connect_args, **kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
