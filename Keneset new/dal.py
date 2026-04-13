"""
Data Access Layer (DAL) - Tier 3
Handles all database connections and SQL queries.
No other layer should contain SQL or direct database access.
"""
import pyodbc# type: ignore
import os


class DatabaseConnection:
    """Manages the connection to the MS Access database and provides
    data retrieval methods for all entities."""

    def __init__(self, db_path: str = None):# type: ignore
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
            self._connection.close()# type: ignore
            self._connection = None

    def _execute(self, query: str, args: tuple = (), one: bool = False):
        """Execute a query and return results as a list of dicts (or a single dict)."""
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
        """Execute an INSERT or UPDATE query and commit the transaction."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, args)
        if return_identity:
            cursor.execute("SELECT @@IDENTITY")
            identity = cursor.fetchone()[0]
            conn.commit()
            return int(identity) if identity else None
        conn.commit()

    # ── Members ─────────────────────────────────────────────────────

    def get_members_count(self) -> int:
        """Return the total number of Knesset members."""
        result = self._execute("SELECT COUNT(*) AS c FROM knesetmembers", one=True)
        return result["c"]# type: ignore

    def get_all_members(self) -> list[dict]:
        """Return all members joined with their party name, ordered alphabetically."""
        return self._execute("""
            SELECT m.knesetmemberID, m.member_name, m.age, m.job, m.photo_url,
                   m.partyID, p.party_name, p.photo_url AS party_logo
            FROM knesetmembers m
            LEFT JOIN parties p ON m.partyID = p.partyID
            ORDER BY m.member_name
        """)# type: ignore

    def get_member_by_id(self, member_id: int) -> dict | None:
        """Return a single member with party info, or None if not found."""
        return self._execute("""
            SELECT m.*, m.photo_url, p.party_name, p.photo_url AS party_logo
            FROM knesetmembers m
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE m.knesetmemberID = ?
        """, (member_id,), one=True)# type: ignore

    def get_members_by_party(self, party_id: int) -> list[dict]:
        """Return all members belonging to a specific party."""
        return self._execute(
            "SELECT * FROM knesetmembers WHERE partyID = ? ORDER BY member_name",
            (party_id,),
        )# type: ignore

    def get_member_laws(self, member_id: int) -> list[dict]:
        """Return all laws associated with a member."""
        return self._execute("""
            SELECT l.lawID, l.law_name
            FROM knesetmemberslaws kl
            INNER JOIN laws l ON kl.lawID = l.lawID
            WHERE kl.knesetmemberID = ?
            ORDER BY l.law_name
        """, (member_id,))# type: ignore

    def get_member_committees(self, member_id: int) -> list[dict]:
        """Return all committees a member belongs to."""
        return self._execute("""
            SELECT c.commitieID, c.commitie_name
            FROM knesetmemberscommities kc
            INNER JOIN commities c ON kc.commitieID = c.commitieID
            WHERE kc.knesetmemberID = ?
            ORDER BY c.commitie_name
        """, (member_id,))# type: ignore

    # ── Parties ─────────────────────────────────────────────────────

    def get_parties_count(self) -> int:
        """Return the total number of parties."""
        result = self._execute("SELECT COUNT(*) AS c FROM parties", one=True)
        return result["c"]# type: ignore

    def get_all_parties(self) -> list[dict]:
        """Return all parties ordered by number of mandates (descending)."""
        return self._execute("SELECT * FROM parties ORDER BY mandates DESC")# type: ignore

    def get_party_by_id(self, party_id: int) -> dict | None:
        """Return a single party or None if not found."""
        return self._execute(
            "SELECT * FROM parties WHERE partyID = ?", (party_id,), one=True
        )# type: ignore

    # ── Committees ──────────────────────────────────────────────────

    def get_committees_count(self) -> int:
        """Return the total number of committees."""
        result = self._execute("SELECT COUNT(*) AS c FROM commities", one=True)
        return result["c"]# type: ignore

    def get_all_committees(self) -> list[dict]:
        """Return all committees ordered by name."""
        return self._execute("SELECT * FROM commities ORDER BY commitie_name")# type: ignore

    def get_committee_by_id(self, committee_id: int) -> dict | None:
        """Return a single committee with leader info, or None if not found."""
        return self._execute("""
            SELECT c.*, m.member_name AS leader_name,
                   m.photo_url AS leader_photo,
                   m.knesetmemberID AS leader_member_id,
                   m.age AS leader_age,
                   m.partyID AS leader_party_id,
                   p.party_name AS leader_party_name,
                   p.photo_url AS leader_party_logo
            FROM (commities c
            LEFT JOIN knesetmembers m ON c.LeaderID = m.knesetmemberID)
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE c.commitieID = ?
        """, (committee_id,), one=True)# type: ignore

    def get_committee_members(self, committee_id: int) -> list[dict]:
        """Return all members belonging to a committee."""
        return self._execute("""
            SELECT m.knesetmemberID, m.member_name, m.age, m.photo_url,
                   m.partyID, p.party_name, p.photo_url AS party_logo
            FROM (knesetmemberscommities kc
            INNER JOIN knesetmembers m ON kc.knesetmemberID = m.knesetmemberID)
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE kc.commitieID = ?
            ORDER BY m.member_name
        """, (committee_id,))# type: ignore

    # ── Laws ────────────────────────────────────────────────────────

    def get_laws_count(self) -> int:
        """Return the total number of laws."""
        result = self._execute("SELECT COUNT(*) AS c FROM laws", one=True)
        return result["c"]# type: ignore

    def get_all_laws(self) -> list[dict]:
        """Return all laws ordered by name."""
        return self._execute("SELECT * FROM laws ORDER BY law_name")# type: ignore

    def get_law_by_id(self, law_id: int) -> dict | None:
        """Return a single law or None if not found."""
        return self._execute(
            "SELECT * FROM laws WHERE lawID = ?", (law_id,), one=True
        )# type: ignore

    def get_law_members(self, law_id: int) -> list[dict]:
        """Return all members associated with a law."""
        return self._execute("""
            SELECT m.knesetmemberID, m.member_name, m.photo_url, m.partyID, p.party_name,
                   p.photo_url AS party_logo
            FROM (knesetmemberslaws kl
            INNER JOIN knesetmembers m ON kl.knesetmemberID = m.knesetmemberID)
            LEFT JOIN parties p ON m.partyID = p.partyID
            WHERE kl.lawID = ?
            ORDER BY m.member_name
        """, (law_id,))# type: ignore

    # ── Login ───────────────────────────────────────────────────────

    def validate_login(self, username: str, password: str) -> dict | None:
        """Return the user row if credentials match, or None."""
        return self._execute(
            "SELECT * FROM login WHERE username = ? AND password = ?",
            (username, password), one=True
        )# type: ignore 

    # ── CRUD: Members ──────────────────────────────────────────────

    def get_next_id(self, tablename: str, id_column: str) -> int:
        """Helper to get highest existing ID + 1 for Access tables without AutoNumber."""
        res = self._execute(f"SELECT MAX({id_column}) AS max_id FROM {tablename}", one=True)
        if res and res["max_id"] is not None:# type: ignore
            return int(res["max_id"]) + 1# type: ignore
        return 1

    def insert_member(self, member_name: str, age: int, job: str,
                      photo_url: str, partyID: int) -> int:
        """Insert a new Knesset member and return its ID."""
        new_id = self.get_next_id("knesetmembers", "knesetmemberID")
        self._execute_write(
            "INSERT INTO knesetmembers (knesetmemberID, member_name, age, job, photo_url, partyID) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_id, member_name, age, job, photo_url, partyID)
        )
        return new_id

    def update_member(self, member_id: int, member_name: str, age: int,
                      job: str, photo_url: str, partyID: int):
        """Update an existing Knesset member."""
        self._execute_write(
            "UPDATE knesetmembers SET member_name=?, age=?, job=?, photo_url=?, partyID=? "
            "WHERE knesetmemberID=?",
            (member_name, age, job, photo_url, partyID, member_id)
        )

    def delete_member(self, member_id: int):
        """Delete a member and clean up its relationships."""
        self.delete_member_committees(member_id)
        self.delete_member_laws(member_id)
        self._execute_write("DELETE FROM knesetmembers WHERE knesetmemberID=?", (member_id,))

    # ── CRUD: Parties ──────────────────────────────────────────────

    def insert_party(self, party_name: str, mandates: int, photo_url: str) -> int:
        """Insert a new party and return its ID."""
        new_id = self.get_next_id("parties", "partyID")
        self._execute_write(
            "INSERT INTO parties (partyID, party_name, mandates, photo_url) VALUES (?, ?, ?, ?)",
            (new_id, party_name, mandates, photo_url)
        )
        return new_id

    def update_party(self, party_id: int, party_name: str, mandates: int,
                     photo_url: str):
        """Update an existing party."""
        self._execute_write(
            "UPDATE parties SET party_name=?, mandates=?, photo_url=? WHERE partyID=?",
            (party_name, mandates, photo_url, party_id)
        )

    def delete_party(self, party_id: int):
        """Delete a party and unset partyID on its members (set to 0)."""
        self.remove_members_from_party(party_id)
        self._execute_write("DELETE FROM parties WHERE partyID=?", (party_id,))

    # ── CRUD: Committees ───────────────────────────────────────────

    def insert_committee(self, commitie_name: str, description: str,
                         LeaderID: int) -> int:
        """Insert a new committee and return its ID."""
        new_id = self.get_next_id("commities", "commitieID")
        self._execute_write(
            "INSERT INTO commities (commitieID, commitie_name, description, LeaderID) "
            "VALUES (?, ?, ?, ?)",
            (new_id, commitie_name, description, LeaderID)
        )
        return new_id

    def update_committee(self, committee_id: int, commitie_name: str,
                         description: str, LeaderID: int):
        """Update an existing committee."""
        self._execute_write(
            "UPDATE commities SET commitie_name=?, description=?, LeaderID=? "
            "WHERE commitieID=?",
            (commitie_name, description, LeaderID, committee_id)
        )

    def delete_committee(self, committee_id: int):
        """Delete a committee and clean up its relationships."""
        self.delete_committee_members(committee_id)
        self._execute_write("DELETE FROM commities WHERE commitieID=?", (committee_id,))

    # ── CRUD: Laws ─────────────────────────────────────────────────

    def insert_law(self, law_name: str, description: str) -> int:
        """Insert a new law and return its ID."""
        new_id = self.get_next_id("laws", "lawID")
        self._execute_write(
            "INSERT INTO laws (lawID, law_name, description) VALUES (?, ?, ?)",
            (new_id, law_name, description)
        )
        return new_id

    def update_law(self, law_id: int, law_name: str, description: str):
        """Update an existing law."""
        self._execute_write(
            "UPDATE laws SET law_name=?, description=? WHERE lawID=?",
            (law_name, description, law_id)
        )

    def delete_law(self, law_id: int):
        """Delete a law and clean up its relationships."""
        self.delete_law_members(law_id)
        self._execute_write("DELETE FROM laws WHERE lawID=?", (law_id,))

    # ── CRUD: Relationships (Junction Tables) ──────────────────────

    def delete_member_committees(self, member_id: int):
        self._execute_write("DELETE FROM knesetmemberscommities WHERE knesetmemberID=?", (member_id,))

    def insert_member_committee(self, member_id: int, committee_id: int):
        self._execute_write("INSERT INTO knesetmemberscommities (knesetmemberID, commitieID) VALUES (?, ?)", (member_id, committee_id))

    def delete_member_laws(self, member_id: int):
        self._execute_write("DELETE FROM knesetmemberslaws WHERE knesetmemberID=?", (member_id,))

    def insert_member_law(self, member_id: int, law_id: int):
        self._execute_write("INSERT INTO knesetmemberslaws (knesetmemberID, lawID) VALUES (?, ?)", (member_id, law_id))

    def delete_committee_members(self, committee_id: int):
        self._execute_write("DELETE FROM knesetmemberscommities WHERE commitieID=?", (committee_id,))

    def delete_law_members(self, law_id: int):
        self._execute_write("DELETE FROM knesetmemberslaws WHERE lawID=?", (law_id,))

    def remove_members_from_party(self, party_id: int):
        """Remove all members from a specific party by setting partyID to 0."""
        self._execute_write("UPDATE knesetmembers SET partyID=0 WHERE partyID=?", (party_id,))

    def set_member_party(self, member_id: int, party_id: int):
        """Set a single member's partyID."""
        self._execute_write("UPDATE knesetmembers SET partyID=? WHERE knesetmemberID=?", (party_id, member_id))
