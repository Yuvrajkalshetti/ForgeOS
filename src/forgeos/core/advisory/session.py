"""Advisory session store.

Groups one advisory lineage — request → recommendation → human decision →
implementation → finding — as a persisted record. Pure bookkeeping: it links
existing ids, and never executes or approves anything.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Sequence

from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.advisory.models import AdvisorySession
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]


class AdvisorySessionStore:
    """Create, read, and append references to advisory sessions."""

    def __init__(self, store: StoragePort, clock: Clock = utcnow) -> None:
        self._store = store
        self._clock = clock

    def start(self, request: str, recommendation_id: str | None = None) -> AdvisorySession:
        now = self._clock().isoformat()
        session = AdvisorySession(
            request=request, recommendation_id=recommendation_id, created_at=now, updated_at=now
        )
        self._save(session)
        return session

    def get(self, session_id: str) -> AdvisorySession | None:
        row = self._store.get(Collections.ADVISORY_SESSIONS, session_id)
        return AdvisorySession.model_validate(row) if row is not None else None

    def attach(
        self,
        session_id: str,
        *,
        decision_id: str | None = None,
        implementation_refs: Sequence[str] | None = None,
        finding_id: str | None = None,
    ) -> AdvisorySession | None:
        """Link a decision, implementation refs, and/or a finding to the session."""
        session = self.get(session_id)
        if session is None:
            return None
        if decision_id is not None:
            session.decision_id = decision_id
        if implementation_refs is not None:
            session.implementation_refs = list(implementation_refs)
        if finding_id is not None:
            session.finding_id = finding_id
        session.updated_at = self._clock().isoformat()
        self._save(session)
        return session

    def list(self) -> list[AdvisorySession]:
        rows = self._store.query(Collections.ADVISORY_SESSIONS)
        sessions = [AdvisorySession.model_validate(r) for r in rows]
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def _save(self, session: AdvisorySession) -> None:
        self._store.put(
            Collections.ADVISORY_SESSIONS, session.id, session.model_dump(mode="json")
        )
