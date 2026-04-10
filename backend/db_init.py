from sqlalchemy import text
from sqlalchemy.engine import Engine


def ensure_schema(engine: Engine) -> None:
    """SQLite 운영 DB에 필요한 컬럼과 초기 데이터를 맞춘다."""
    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(exit_passes)")).fetchall()
        }

        if "number" not in columns:
            conn.execute(text("ALTER TABLE exit_passes ADD COLUMN number INTEGER"))
            conn.execute(text("UPDATE exit_passes SET number = id WHERE number IS NULL"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_exit_passes_number ON exit_passes (number)"))

