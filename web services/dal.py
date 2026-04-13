"""
Data Access Layer (DAL) – Deot (Opinions) Web Service
======================================================
Handles all database connections and queries for the Deot database.
Uses MS Access (Deot.mdb) with the following table:

Table: Deot
  - DeaId     (COUNTER)  — Auto-increment primary key
  - dateOfDea (DATETIME) — Date the opinion was published
  - name      (VARCHAR)  — Author name
  - title     (VARCHAR)  — Opinion title
  - content   (LONGCHAR) — Opinion content
"""
import pyodbc  # type: ignore
import os


class DeotDatabase:
    """Manages connection to the Deot MS Access database."""

    def __init__(self, db_path: str = None):  # type: ignore
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Deot.mdb")
        self._conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            f"DBQ={db_path};"
        )
        self._connection = None

    # ── Connection management ───────────────────────────────────────

    def connect(self):
        """Open a connection to the database."""
        if self._connection is None:
            self._connection = pyodbc.connect(self._conn_str)
        return self._connection

    def close(self):
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()  # type: ignore
            self._connection = None

    def _execute(self, query: str, args: tuple = (), one: bool = False):
        """Execute a SELECT query and return results as list of dicts."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, args)
        try:
            columns = [col[0] for col in cursor.description]
            rows = [
                {k: (v.strip() if isinstance(v, str) else v) for k, v in zip(columns, row)}
                for row in cursor.fetchall()
            ]
            return (rows[0] if rows else None) if one else rows
        except pyodbc.ProgrammingError:
            return None

    def _execute_write(self, query: str, args: tuple = (), return_identity: bool = False):
        """Execute an INSERT / UPDATE / DELETE and commit."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, args)
        if return_identity:
            cursor.execute("SELECT @@IDENTITY")
            identity = cursor.fetchone()[0]
            conn.commit()
            return int(identity) if identity else None
        conn.commit()

    # ── Read operations ─────────────────────────────────────────────

    def get_all_deot(self) -> list[dict]:
        """Return all opinions, newest first."""
        return self._execute(
            "SELECT * FROM Deot ORDER BY dateOfDea DESC"
        )  # type: ignore

    def get_dea_by_id(self, dea_id: int) -> dict | None:
        """Return a single opinion by its ID."""
        return self._execute(
            "SELECT * FROM Deot WHERE DeaId = ?",
            (dea_id,),
            one=True,
        )  # type: ignore

    def get_deot_count(self) -> int:
        """Return the total number of opinions."""
        result = self._execute("SELECT COUNT(*) AS c FROM Deot", one=True)
        return result["c"] if result else 0  # type: ignore

    # ── Write operations ────────────────────────────────────────────

    def add_dea(self, name: str, title: str, content: str, dateOfDea: str) -> int:
        """Insert a new opinion and return its ID."""
        return self._execute_write(
            "INSERT INTO Deot (name, title, content, dateOfDea) "
            "VALUES (?, ?, ?, ?)",
            (name, title, content, dateOfDea),
            return_identity=True,
        )  # type: ignore

    def delete_dea(self, dea_id: int):
        """Delete an opinion by its ID."""
        self._execute_write("DELETE FROM Deot WHERE DeaId = ?", (dea_id,))
