"""ClientAgent — core behavioural agent for optical retail simulation.

Each ClientAgent represents a single end-customer who periodically visits
a store, picks an optical product gamme (ESSENTIEL → PRESTIGE), and
generates a sale ticket.

P3 Task 4.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import mesa

from src.simulation.archetypes import GAMME_ORDERED

if TYPE_CHECKING:
    from src.simulation.agents.store import StoreAgent
    from src.simulation.archetypes import ArchetypeParams

# Gamme ticket multipliers (relative to archetype mean_ticket)
_GAMME_TICKET_MULTIPLIER: dict[str, float] = {
    "ESSENTIEL": 0.7,
    "CONFORT": 0.9,
    "PREMIUM": 1.3,
    "PRESTIGE": 1.8,
}

# Price elasticity: -0.5 means 10% price drop → 5% demand increase
_PRICE_ELASTICITY: float = -0.5

# Log-normal sigma for ticket sampling
_TICKET_SIGMA: float = 0.20


class ClientAgent(mesa.Agent):
    """Represents a single optical retail client in the simulation.

    Attributes
    ----------
    archetype : ArchetypeParams
        The behavioural archetype governing purchase timing and preferences.
    home_store_name : str
        Primary store city name.
    conventionnement : str
        Insurance convention type (e.g. "LIBRE", "CMU").
    age : int
        Client age in years.
    last_purchase_step : int
        Simulation step of the most recent purchase (-N for pre-sim history).
    last_purchase_gamme : str | None
        Gamme of the most recent purchase, or None if no purchase yet.
    personal_interval : float
        Personalised purchase interval (archetype interval +/- noise).
    """

    def __init__(
        self,
        model: mesa.Model,
        *,
        archetype: ArchetypeParams,
        home_store_name: str,
        conventionnement: str,
        age: int,
        last_purchase_step: int,
    ) -> None:
        super().__init__(model)
        self.archetype: ArchetypeParams = archetype
        self.home_store_name: str = home_store_name
        self.conventionnement: str = conventionnement
        self.age: int = age
        self.last_purchase_step: int = last_purchase_step
        self.last_purchase_gamme: str | None = None

        # Personal interval: archetype interval +/- ~15% noise
        noise = model.random.gauss(0, 0.15 * archetype.purchase_interval_months)
        self.personal_interval: float = max(
            1.0, archetype.purchase_interval_months + noise
        )

        # Word-of-mouth: contacts are populated by the model after init
        self.contacts: list[ClientAgent] = []
        self.premium_boost: float = 0.0

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Execute one simulation step (= 1 month).

        Pseudo-code from Spec §8.2:
        1. Check if enough time has passed since last purchase.
        2. Roll hazard × seasonality to decide if purchase occurs.
        3. Choose store (home or switch).
        4. Compute gamme probability distribution (effort + price modulation).
        5. Sample gamme and ticket amount.
        6. Record the sale.
        """
        current_step: int = self.model.current_step

        # 1. Purchase interval guard
        months_since = current_step - self.last_purchase_step
        if months_since < self.personal_interval:
            return

        # 2. Hazard × seasonality check
        current_month = ((current_step - 1) % 12) + 1
        seasonality_coeff = self.model.seasonality.get(current_month, 1.0)
        p_buy = self.archetype.hazard_base * seasonality_coeff
        if self.model.random.random() > p_buy:
            return

        # 3. Choose store
        store = self._choose_store()

        # 4. Compute gamme probabilities with effort/price modulation
        gamme_probs = self._compute_gamme_probs(store)

        # 5. Sample gamme
        gamme = self._sample_gamme(gamme_probs)

        # 6. Sample ticket
        ticket = self._sample_ticket(gamme)

        # 7. Record sale
        self._record_sale(store, gamme, ticket, current_step)

        # 8. Word-of-mouth: boost contacts after Premium/Prestige purchase
        if (
            gamme in ("PREMIUM", "PRESTIGE")
            and getattr(self.model, "enable_word_of_mouth", False)
            and self.contacts
        ):
            for contact in self.contacts:
                contact.premium_boost += 0.10

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _choose_store(self) -> StoreAgent:
        """Pick the store where the purchase happens.

        With probability `switch_prob` the client visits a random other store
        instead of their home store.
        """
        stores = self.model.stores
        if (
            self.archetype.switch_prob > 0
            and len(stores) > 1
            and self.model.random.random() < self.archetype.switch_prob
        ):
            other_names = [n for n in stores if n != self.home_store_name]
            chosen_name = self.model.random.choice(other_names)
            return stores[chosen_name]
        return stores[self.home_store_name]

    def _compute_gamme_probs(self, store: StoreAgent) -> dict[str, float]:
        """Compute final gamme probabilities after effort and price modulation.

        Effort boost: commercial effort > 1 shifts probability mass from
        lower gammes (ESSENTIEL, CONFORT) toward upper gammes (PREMIUM,
        PRESTIGE).

        Price elasticity: a price multiplier < 1.0 on a gamme increases its
        relative probability (elasticity = -0.5).

        Returns a normalised probability dict over GAMME_ORDERED.
        """
        base_probs = dict(self.archetype.gamme_distribution)
        effort = store.get_effort(self.archetype.archetype_id)

        # --- Effort modulation ---
        # effort > 1 boosts premium gammes; effort < 1 does the opposite
        if effort != 1.0:
            boost = effort - 1.0  # e.g. +0.3 for effort=1.3
            for g in GAMME_ORDERED:
                if g in ("PREMIUM", "PRESTIGE"):
                    base_probs[g] *= 1.0 + boost
                else:
                    base_probs[g] *= 1.0 - boost * 0.5

        # Clamp to non-negative
        for g in GAMME_ORDERED:
            base_probs[g] = max(base_probs[g], 0.0)

        # --- Word-of-mouth boost ---
        if self.premium_boost > 0:
            base_probs["PREMIUM"] *= 1.0 + self.premium_boost
            base_probs["PRESTIGE"] *= 1.0 + self.premium_boost

        # --- Price elasticity modulation ---
        for g in GAMME_ORDERED:
            price_mult = store.get_price_multiplier(g)
            if price_mult != 1.0:
                # elasticity = -0.5: demand_change = elasticity * price_change
                # price_change = price_mult - 1.0
                demand_factor = 1.0 + _PRICE_ELASTICITY * (price_mult - 1.0)
                base_probs[g] *= max(demand_factor, 0.0)

        # --- Normalise ---
        total = sum(base_probs.values())
        if total > 0:
            for g in GAMME_ORDERED:
                base_probs[g] /= total
        else:
            # Fallback to uniform
            for g in GAMME_ORDERED:
                base_probs[g] = 1.0 / len(GAMME_ORDERED)

        return base_probs

    def _sample_gamme(self, probs: dict[str, float]) -> str:
        """Sample a gamme from the probability distribution.

        Uses a cumulative-sum approach with the model's seeded RNG.
        """
        r = self.model.random.random()
        cumulative = 0.0
        for g in GAMME_ORDERED:
            cumulative += probs.get(g, 0.0)
            if r <= cumulative:
                return g
        # Numerical safety: return last gamme
        return GAMME_ORDERED[-1]

    def _sample_ticket(self, gamme: str) -> float:
        """Sample a ticket amount from a log-normal distribution.

        Mean = archetype.mean_ticket × gamme multiplier.
        """
        gamme_mult = _GAMME_TICKET_MULTIPLIER.get(gamme, 1.0)
        mean = self.archetype.mean_ticket * gamme_mult

        # Log-normal parameterisation: mu and sigma of the underlying normal
        # so that E[X] = mean and CV ~ _TICKET_SIGMA
        sigma_sq = math.log(1.0 + _TICKET_SIGMA**2)
        mu = math.log(mean) - sigma_sq / 2.0
        sigma = math.sqrt(sigma_sq)

        ticket = self.model.random.lognormvariate(mu, sigma)
        return round(max(ticket, 1.0), 2)

    def _record_sale(
        self,
        store: StoreAgent,
        gamme: str,
        ticket: float,
        step: int,
    ) -> None:
        """Append the sale record to the model's sales log and update state."""
        self.model.sales_log.append(
            {
                "step": step,
                "store": store.store_name,
                "client_id": self.unique_id,
                "archetype_id": self.archetype.archetype_id,
                "gamme": gamme,
                "ticket": ticket,
                "conventionnement": self.conventionnement,
                "age": self.age,
            }
        )
        self.last_purchase_step = step
        self.last_purchase_gamme = gamme
