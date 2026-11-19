import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
SEED_PATH = Path(__file__).with_name("seed.sql")


class Database:
    """Owns the SQLite connection and the transaction boundary."""

    def __init__(self, path):
        # isolation_level=None: we issue BEGIN, COMMIT and ROLLBACK ourselves.
        self._conn = sqlite3.connect(str(path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._depth = 0

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def create_schema(self) -> None:
        self._conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def load_seed(self) -> None:
        self._conn.executescript(SEED_PATH.read_text(encoding="utf-8"))

    @contextmanager
    def transaction(self):
        """BEGIN ... COMMIT, or ROLLBACK if anything raises. Nested use joins the outer one."""
        if self._depth > 0:
            yield self._conn
            return
        self._conn.execute("BEGIN")
        self._depth = 1
        try:
            yield self._conn
            self._conn.execute("COMMIT")
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        finally:
            self._depth = 0

    def close(self) -> None:
        self._conn.close()
