"""Simulation calendar and date conversion utilities."""

from __future__ import annotations

from dataclasses import dataclass

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


@dataclass(frozen=True, slots=True)
class SimDate:
    """Represents simulation date and provides conversions."""

    year: int
    month: int  # 1 to 12

    @classmethod
    def from_tick(cls, tick: int, start_year: int = 2000, tick_months: int = 1) -> SimDate:
        total_months = tick * tick_months
        year = start_year + (total_months // 12)
        month = (total_months % 12) + 1
        return cls(year=year, month=month)

    def to_tick(self, start_year: int = 2000, tick_months: int = 1) -> int:
        total_months = (self.year - start_year) * 12 + (self.month - 1)
        return total_months // tick_months

    @property
    def month_name(self) -> str:
        return MONTH_NAMES[self.month - 1]

    def format(self) -> str:
        return f"{self.month_name} {self.year}"

    def iso(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __str__(self) -> str:
        return self.format()
