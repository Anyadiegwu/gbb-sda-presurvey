from sqlmodel import SQLModel, Session, create_engine
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create tables. In production, use Alembic migrations instead."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
