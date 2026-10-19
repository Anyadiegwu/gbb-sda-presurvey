from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def init_db() -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    except Exception as exc:
        raise RuntimeError(
            "Could not enable PostGIS. Make sure PostGIS is installed on your "
            "Postgres server (use the postgis/postgis Docker image, or install it "
            "with Stack Builder on Windows) and that your DB user may create extensions."
        ) from exc

    SQLModel.metadata.create_all(engine)
    _apply_dev_migrations()


def _apply_dev_migrations() -> None:
    """Idempotent upgrades for databases created before nodes had a type.

    create_all() only creates missing *tables*; it never adds columns to an
    existing one. These statements are safe to run on every startup. Replace
    with Alembic migrations before production.
    """
    statements = [
        "ALTER TABLE manholes ADD COLUMN IF NOT EXISTS node_type VARCHAR NOT NULL DEFAULT 'MH'",
        "ALTER TABLE manholes ADD COLUMN IF NOT EXISTS source_file VARCHAR",
        "ALTER TABLE manholes ADD COLUMN IF NOT EXISTS folder VARCHAR",
        "CREATE INDEX IF NOT EXISTS ix_manholes_node_type ON manholes (node_type)",
        "CREATE INDEX IF NOT EXISTS ix_manholes_source_file ON manholes (source_file)",
        "CREATE INDEX IF NOT EXISTS ix_fiber_routes_source_file ON fiber_routes (source_file)",
        # Spatial (KNN) index so "nearest node" stays fast with thousands of
        # nodes, without keeping a separate geometry column in sync with
        # latitude/longitude.
        "CREATE INDEX IF NOT EXISTS ix_manholes_point ON manholes "
        "USING gist (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326))",
    ]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
        