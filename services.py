"""
Business Logic Layer (BLL) - Tier 2
Contains business logic and data processing.
Calls the Data Access Layer — never writes SQL directly.
"""
from dal import DatabaseConnection


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
