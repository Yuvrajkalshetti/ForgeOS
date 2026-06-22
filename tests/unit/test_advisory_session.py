from __future__ import annotations

from forgeos.core.advisory import AdvisorySessionStore
from forgeos.testing.fakes import InMemoryStorage


def test_session_lineage_grouping() -> None:
    store = AdvisorySessionStore(InMemoryStorage())
    session = store.start("build feature X", recommendation_id="mrec_1")
    assert session.recommendation_id == "mrec_1"
    assert session.decision_id is None

    updated = store.attach(
        session.id,
        decision_id="dec_1",
        implementation_refs=["file:a.py", "file:b.py"],
        finding_id="afind_1",
    )
    assert updated is not None
    assert updated.decision_id == "dec_1"
    assert updated.implementation_refs == ["file:a.py", "file:b.py"]
    assert updated.finding_id == "afind_1"


def test_attach_to_missing_session_returns_none() -> None:
    store = AdvisorySessionStore(InMemoryStorage())
    assert store.attach("nope", finding_id="x") is None


def test_list_orders_newest_first() -> None:
    store = AdvisorySessionStore(InMemoryStorage())
    import datetime

    clocks = iter(
        [datetime.datetime(2026, 1, d, tzinfo=datetime.UTC) for d in (1, 2)] * 2
    )
    s = AdvisorySessionStore(InMemoryStorage(), clock=lambda: next(clocks))
    a = s.start("first")
    b = s.start("second")
    listed = s.list()
    assert [x.id for x in listed][:2] == [b.id, a.id]
