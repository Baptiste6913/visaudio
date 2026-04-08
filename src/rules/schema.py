"""Pydantic schema for declarative diagnostic rules."""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    scope: Literal["network", "store", "segment"]
    severity: Severity
    condition: str = Field(
        min_length=1,
        description="Python expression evaluated against a context dict.",
    )
    finding: str = Field(min_length=1, description="Template for the finding text.")
    recommendation: Optional[str] = None
