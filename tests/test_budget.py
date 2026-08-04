import math

import pytest

from src.utils.budget import BudgetExceeded, BudgetGuard


def test_budget_guard_initial_state() -> None:
    guard = BudgetGuard(10.0)

    assert guard.limit == 10.0
    assert guard.spent == 0.0
    assert guard.remaining == 10.0


def test_budget_guard_allows_exact_limit() -> None:
    guard = BudgetGuard(0.3)

    assert guard.charge(0.1) == 0.1
    assert guard.charge(0.2) == 0.3
    assert guard.remaining == 0.0


def test_budget_guard_records_overage() -> None:
    guard = BudgetGuard(1.0)

    guard.charge(0.75)
    with pytest.raises(BudgetExceeded, match=r"spent=1.25, limit=1.0"):
        guard.charge(0.5)

    assert guard.spent == 1.25
    assert guard.remaining == 0.0


@pytest.mark.parametrize("invalid", [-1.0, math.nan, math.inf, -math.inf])
def test_budget_guard_rejects_invalid_limit(invalid: float) -> None:
    with pytest.raises(ValueError, match="limit must be finite and non-negative"):
        BudgetGuard(invalid)


@pytest.mark.parametrize("invalid", [-1.0, math.nan, math.inf, -math.inf])
def test_budget_guard_rejects_invalid_charge(invalid: float) -> None:
    guard = BudgetGuard(1.0)

    with pytest.raises(ValueError, match="cost must be finite and non-negative"):
        guard.charge(invalid)

    assert guard.spent == 0.0