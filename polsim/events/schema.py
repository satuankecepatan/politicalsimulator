"""Pydantic schema for data-driven events and effects."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EffectDef(StrictModel):
    target: Literal["economy", "party", "cohort", "government", "relations"]
    parameter: str
    delta: float
    target_id: str | None = None  # None = active leader / all cohorts / national
    duration_ticks: int = Field(default=1, ge=1)


class EventDef(StrictModel):
    id: str
    title: str
    description: str
    category: str
    base_prob: float = Field(ge=0.0, le=1.0)
    precondition: str | None = None
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    effects: list[EffectDef] = Field(default_factory=list)
    follow_up_events: list[str] = Field(default_factory=list)
    follow_up_delay_ticks: int = 0
