"""
Data Access Layer (DAL) - Tier 3
Handles all database connections and SQL queries.
No other layer should contain SQL or direct database access.
"""
import pyodbc
import os


class DatabaseConnection:
    """Manages the connection to the MS Access database and provides
    data retrieval methods for all entities."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "Eliezer.mdb")
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
            self._connection.close()
            self._connection = None

    def _execute(self, query: str, args: tuple = (), one: bool = False):
        """Execute a query and return results as a list of dicts (or a single dict)."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, args)
        try:
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return (rows[0] if rows else None) if one else rows
        except pyodbc.ProgrammingError:
            return None

    # ── Members ─────────────────────────────────────────────────────

    def get_members_count(self) -> int:
        """Return the total number of Knesset members."""
        result = self._execute("SELECT COUNT(*) AS c FROM knesetmembers", one=True)
        return result["c"]

    def get_all_members(self) -> list[dict]:
        """Return all members joined with their party name, ordered alphabetically."""
        return self._execute("""
            SELECT m.knesetmemberID, m.member_name, m.age, m.job, m.photo_url,
                   m.partyID, p.party_name
            FROM knesetmembers m
            LEFT JOIN parties p ON m.partyID = p.partyID
            ORDER BY m.member_name
        """)

    def get_member_by_id(self, member_id: int) -> dict | None:
        """Return a single member with party info, or None if not found."""
        return self._execute("""
            SELECT m.*, m.photo_url, p.party_name
            FROM knesetmembers m
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE m.knesetmemberID = ?
        """, (member_id,), one=True)

    def get_members_by_party(self, party_id: int) -> list[dict]:
        """Return all members belonging to a specific party."""
        return self._execute(
            "SELECT * FROM knesetmembers WHERE partyID = ? ORDER BY member_name",
            (party_id,),
        )

    def get_member_laws(self, member_id: int) -> list[dict]:
        """Return all laws associated with a member."""
        return self._execute("""
            SELECT l.lawID, l.law_name
            FROM knesetmemberslaws kl
            INNER JOIN laws l ON kl.lawID = l.lawID
            WHERE kl.knesetmemberID = ?
            ORDER BY l.law_name
        """, (member_id,))

    def get_member_committees(self, member_id: int) -> list[dict]:
        """Return all committees a member belongs to."""
        return self._execute("""
            SELECT c.commitieID, c.commitie_name
            FROM knesetmemberscommities kc
            INNER JOIN commities c ON kc.commitieID = c.commitieID
            WHERE kc.knesetmemberID = ?
            ORDER BY c.commitie_name
        """, (member_id,))

    # ── Parties ─────────────────────────────────────────────────────

    def get_parties_count(self) -> int:
        """Return the total number of parties."""
        result = self._execute("SELECT COUNT(*) AS c FROM parties", one=True)
        return result["c"]

    def get_all_parties(self) -> list[dict]:
        """Return all parties ordered by number of mandates (descending)."""
        return self._execute("SELECT * FROM parties ORDER BY mandates DESC")

    def get_party_by_id(self, party_id: int) -> dict | None:
        """Return a single party or None if not found."""
        return self._execute(
            "SELECT * FROM parties WHERE partyID = ?", (party_id,), one=True
        )

    # ── Committees ──────────────────────────────────────────────────

    def get_committees_count(self) -> int:
        """Return the total number of committees."""
        result = self._execute("SELECT COUNT(*) AS c FROM commities", one=True)
        return result["c"]

    def get_all_committees(self) -> list[dict]:
        """Return all committees ordered by name."""
        return self._execute("SELECT * FROM commities ORDER BY commitie_name")

    def get_committee_by_id(self, committee_id: int) -> dict | None:
        """Return a single committee or None if not found."""
        return self._execute(
            "SELECT * FROM commities WHERE commitieID = ?",
            (committee_id,), one=True,
        )

    def get_committee_members(self, committee_id: int) -> list[dict]:
        """Return all members belonging to a committee."""
        return self._execute("""
            SELECT m.knesetmemberID, m.member_name, m.age, m.photo_url,
                   m.partyID, p.party_name
            FROM (knesetmemberscommities kc
            INNER JOIN knesetmembers m ON kc.knesetmemberID = m.knesetmemberID)
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE kc.commitieID = ?
            ORDER BY m.member_name
        """, (committee_id,))

    # ── Laws ────────────────────────────────────────────────────────

    def get_laws_count(self) -> int:
        """Return the total number of laws."""
        result = self._execute("SELECT COUNT(*) AS c FROM laws", one=True)
        return result["c"]

    def get_all_laws(self) -> list[dict]:
        """Return all laws ordered by name."""
        return self._execute("SELECT * FROM laws ORDER BY law_name")

    def get_law_by_id(self, law_id: int) -> dict | None:
        """Return a single law or None if not found."""
        return self._execute(
            "SELECT * FROM laws WHERE lawID = ?", (law_id,), one=True
        )

    def get_law_members(self, law_id: int) -> list[dict]:
        """Return all members associated with a law."""
        return self._execute("""
            SELECT m.knesetmemberID, m.member_name, m.photo_url, m.partyID, p.party_name
            FROM (knesetmemberslaws kl
            INNER JOIN knesetmembers m ON kl.knesetmemberID = m.knesetmemberID)
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE kl.lawID = ?
            ORDER BY m.member_name
        """, (law_id,))
