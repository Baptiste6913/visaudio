"""StoreAgent — passive parameter holder for one optical retail store.

Phase 1: holds per-store configuration (effort levels, price multipliers,
active campaigns).  No behavioural logic yet.

P3 Task 3.
"""
from __future__ import annotations

import mesa


class StoreAgent(mesa.Agent):
    """Represents a single store in the simulation.

    Attributes
    ----------
    store_name : str
        Human-readable city name (one of the 6 cities).
    effort_commercial_level : dict[int, float]
        archetype_id -> commercial effort multiplier (default 1.0).
    price_multipliers : dict[str, float]
        gamme -> price multiplier (default 1.0).
    active_campaigns : list[dict]
        Currently active promotional campaigns.
    """

    def __init__(
        self,
        model: mesa.Model,
        *,
        store_name: str,
        effort_commercial_level: dict[int, float] | None = None,
        price_multipliers: dict[str, float] | None = None,
        active_campaigns: list[dict] | None = None,
    ) -> None:
        super().__init__(model)
        self.store_name = store_name
        self.effort_commercial_level: dict[int, float] = (
            effort_commercial_level if effort_commercial_level is not None else {}
        )
        self.price_multipliers: dict[str, float] = (
            price_multipliers if price_multipliers is not None else {}
        )
        self.active_campaigns: list[dict] = (
            active_campaigns if active_campaigns is not None else []
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_effort(self, archetype_id: int) -> float:
        """Return the commercial effort multiplier for *archetype_id*.

        Defaults to 1.0 (neutral) when no specific value has been set.
        """
        return self.effort_commercial_level.get(archetype_id, 1.0)

    def get_price_multiplier(self, gamme: str) -> float:
        """Return the price multiplier for *gamme*.

        Defaults to 1.0 (neutral) when no specific value has been set.
        """
        return self.price_multipliers.get(gamme, 1.0)
