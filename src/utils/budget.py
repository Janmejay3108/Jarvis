from __future__ import annotations

import math
from decimal import Decimal


class BudgetExceeded(RuntimeError):
	pass


def _decimal_amount(value: float, name: str) -> Decimal:
	if not math.isfinite(value) or value < 0:
		raise ValueError(f"{name} must be finite and non-negative")
	return Decimal(str(value))


class BudgetGuard:
	def __init__(self, limit: float) -> None:
		self._limit = _decimal_amount(limit, "limit")
		self._spent = Decimal(0)

	@property
	def limit(self) -> float:
		return float(self._limit)

	@property
	def spent(self) -> float:
		return float(self._spent)

	@property
	def remaining(self) -> float:
		return float(max(self._limit - self._spent, Decimal(0)))

	def charge(self, cost: float) -> float:
		self._spent += _decimal_amount(cost, "cost")
		if self._spent > self._limit:
			raise BudgetExceeded(
				f"budget exceeded: spent={self._spent}, limit={self._limit}"
			)
		return float(self._spent)
