from __future__ import annotations

from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.ports.provider import Message
from forgeos.ports.tokenizer import TokenizerPort


def test_satisfies_tokenizer_protocol() -> None:
    estimator: TokenizerPort = LocalEstimator()
    assert estimator.count_text("abcd") == 1


def test_count_text_is_deterministic_and_length_based() -> None:
    est = LocalEstimator()
    assert est.count_text("") == 0
    assert est.count_text("abcd") == 1
    assert est.count_text("abcde") == 2
    assert est.count_text("a" * 40) == 10
    assert est.count_text("hello") == est.count_text("hello")


def test_count_messages_sums() -> None:
    est = LocalEstimator()
    msgs = [Message("user", "abcd"), Message("user", "abcdefgh")]
    assert est.count_messages(msgs) == 1 + 2
