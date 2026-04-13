"""
Business Logic Layer (BLL) - Tier 2
Contains business logic and data processing.
Calls the Data Access Layer — never writes SQL directly.
"""
from dal import DatabaseConnection# type: ignore


class KnessetService:
    """Provides business-level operations on Knesset data
    by delegating to the DatabaseConnection (DAL)."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    # ── Dashboard ───────────────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        """Return aggregated statistics for the homepage dashboard."""
        return {
            "members": self._db.get_members_count(),
            "parties": self._db.get_parties_count(),
            "committees": self._db.get_committees_count(),
            "laws": self._db.get_laws_count(),
        }

    # ── Members ─────────────────────────────────────────────────────

    def get_all_members(self) -> list[dict]:
        """Return every Knesset member with party info."""
        return self._db.get_all_members()

    def get_member_details(self, member_id: int) -> dict | None:
        """Return full member details including related laws and committees.
        Returns None if the member does not exist."""
        member = self._db.get_member_by_id(member_id)
        if member is None:
            return None
        return {
            "member": member,
            "laws": self._db.get_member_laws(member_id),
            "committees": self._db.get_member_committees(member_id),
        }

    # ── Parties ─────────────────────────────────────────────────────

    def get_all_parties(self) -> list[dict]:
        """Return all parties sorted by mandates."""
        return self._db.get_all_parties()

    def get_party_details(self, party_id: int) -> dict | None:
        """Return a party and its members, or None if not found."""
        party = self._db.get_party_by_id(party_id)
        if party is None:
            return None
        return {
            "party": party,
            "members": self._db.get_members_by_party(party_id),
        }

    # ── Committees ──────────────────────────────────────────────────

    def get_all_committees(self) -> list[dict]:
        """Return all committees sorted by name."""
        return self._db.get_all_committees()

    def get_committee_details(self, committee_id: int) -> dict | None:
        """Return a committee and its members, or None if not found."""
        committee = self._db.get_committee_by_id(committee_id)
        if committee is None:
            return None
        return {
            "committee": committee,
            "members": self._db.get_committee_members(committee_id),
        }

    # ── Laws ────────────────────────────────────────────────────────

    def get_all_laws(self) -> list[dict]:
        """Return all laws sorted by name."""
        return self._db.get_all_laws()

    def get_law_details(self, law_id: int) -> dict | None:
        """Return a law and its associated members, or None if not found."""
        law = self._db.get_law_by_id(law_id)
        if law is None:
            return None
        return {
            "law": law,
            "members": self._db.get_law_members(law_id),
        }

    # ── Authentication ─────────────────────────────────────────────

    def authenticate(self, username: str, password: str) -> bool:
        """Return True if the credentials are valid."""
        return self._db.validate_login(username, password) is not None

    # ── Admin: Data for dashboard ──────────────────────────────────

    def get_admin_data(self) -> dict:
        """Return all entities, including relationship IDs for edit forms."""
        members = self._db.get_all_members()
        if members:
            for m in members:
                m_id = m.get("knesetmemberID")
                if m_id is not None:
                    c_list = self._db.get_member_committees(m_id) or []
                    m["committee_ids"] = [c["commitieID"] for c in c_list]
                    l_list = self._db.get_member_laws(m_id) or []
                    m["law_ids"] = [l["lawID"] for l in l_list]
        
        committees = self._db.get_all_committees()
        if committees:
            for c in committees:
                c_id = c.get("commitieID")
                if c_id is not None:
                    m_list = self._db.get_committee_members(c_id) or []
                    c["member_ids"] = [m["knesetmemberID"] for m in m_list]
            
        laws = self._db.get_all_laws()
        if laws:
            for l in laws:
                l_id = l.get("lawID")
                if l_id is not None:
                    m_list = self._db.get_law_members(l_id) or []
                    l["member_ids"] = [m["knesetmemberID"] for m in m_list]

        parties = self._db.get_all_parties()
        if parties:
            for p in parties:
                p["member_ids"] = [m["knesetmemberID"] for m in members if m.get("partyID") == p.get("partyID")]

        return {
            "members": members or [],
            "parties": parties or [],
            "committees": committees or [],
            "laws": laws or [],
        }

    # ── Admin CRUD: Members ────────────────────────────────────────

    def create_member(self, member_name: str, age: int, job: str,
                      photo_url: str, partyID: int, committee_ids: list[int] = [], law_ids: list[int] = []):
        """Create a new Knesset member."""
        member_id = self._db.insert_member(member_name, age, job, photo_url, partyID)
        if member_id:
            for c_id in committee_ids:
                self._db.insert_member_committee(member_id, c_id)
            for l_id in law_ids:
                self._db.insert_member_law(member_id, l_id)

    def update_member(self, member_id: int, member_name: str, age: int,
                      job: str, photo_url: str, partyID: int, committee_ids: list[int] = [], law_ids: list[int] = []):
        """Update an existing Knesset member."""
        self._db.update_member(member_id, member_name, age, job, photo_url, partyID)
        self._db.delete_member_committees(member_id)
        for c_id in committee_ids:
            self._db.insert_member_committee(member_id, c_id)
        self._db.delete_member_laws(member_id)
        for l_id in law_ids:
            self._db.insert_member_law(member_id, l_id)

    def delete_member(self, member_id: int):
        """Delete a Knesset member."""
        self._db.delete_member(member_id)

    # ── Admin CRUD: Parties ────────────────────────────────────────

    def create_party(self, party_name: str, mandates: int, photo_url: str, member_ids: list[int] = []):
        """Create a new party."""
        party_id = self._db.insert_party(party_name, mandates, photo_url)
        if party_id:
            for m_id in member_ids:
                self._db.set_member_party(m_id, party_id)

    def update_party(self, party_id: int, party_name: str, mandates: int,
                     photo_url: str, member_ids: list[int] = []):
        """Update an existing party."""
        self._db.update_party(party_id, party_name, mandates, photo_url)
        self._db.remove_members_from_party(party_id)
        for m_id in member_ids:
            self._db.set_member_party(m_id, party_id)

    def delete_party(self, party_id: int):
        """Delete a party."""
        self._db.delete_party(party_id)

    # ── Admin CRUD: Committees ─────────────────────────────────────

    def create_committee(self, commitie_name: str, description: str,
                         LeaderID: int, member_ids: list[int] = []):
        """Create a new committee."""
        committee_id = self._db.insert_committee(commitie_name, description, LeaderID)
        if committee_id:
            for m_id in member_ids:
                self._db.insert_member_committee(m_id, committee_id)

    def update_committee(self, committee_id: int, commitie_name: str,
                         description: str, LeaderID: int, member_ids: list[int] = []):
        """Update an existing committee."""
        self._db.update_committee(committee_id, commitie_name, description, LeaderID)
        self._db.delete_committee_members(committee_id)
        for m_id in member_ids:
            self._db.insert_member_committee(m_id, committee_id)

    def delete_committee(self, committee_id: int):
        """Delete a committee."""
        self._db.delete_committee(committee_id)

    # ── Admin CRUD: Laws ───────────────────────────────────────────

    def create_law(self, law_name: str, description: str, member_ids: list[int] = []):
        """Create a new law."""
        law_id = self._db.insert_law(law_name, description)
        if law_id:
            for m_id in member_ids:
                self._db.insert_member_law(m_id, law_id)

    def update_law(self, law_id: int, law_name: str, description: str, member_ids: list[int] = []):
        """Update an existing law."""
        self._db.update_law(law_id, law_name, description)
        self._db.delete_law_members(law_id)
        for m_id in member_ids:
            self._db.insert_member_law(m_id, law_id)

    def delete_law(self, law_id: int):
        """Delete a law."""
        self._db.delete_law(law_id)
