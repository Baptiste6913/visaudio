"""Load K-Means archetypes and derive agent-level behavioural params."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

GAMME_ORDERED: list[str] = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


@dataclass(frozen=True)
class ArchetypeParams:
    """Behavioural parameters for one client archetype."""

    archetype_id: int
    label: str
    n_clients: int

    # Purchase timing
    purchase_interval_months: float
    hazard_base: float

    # Gamme choice
    gamme_distribution: dict[str, float]

    # Store switching
    switch_prob: float

    # Ticket
    mean_ticket: float


def load_archetypes_from_payload(payload: dict) -> dict[int, ArchetypeParams]:
    """Convert the archetypes.json payload into ArchetypeParams per archetype."""
    result: dict[int, ArchetypeParams] = {}
    for arch in payload["archetypes"]:
        centroid = arch["centroid"]

        interval = max(centroid.get("mois_entre_achats", 24.0), 1.0)
        hazard = min(1.0 / interval, 1.0)
        pp = centroid.get("part_premium_plus", 0.0)
        gamme_dist = _derive_gamme_distribution(pp)

        n_achats = centroid.get("n_achats_totaux", 1.0)
        switch = max(0.02, min(0.3, 0.15 / max(n_achats, 0.5)))

        result[int(arch["id"])] = ArchetypeParams(
            archetype_id=int(arch["id"]),
            label=str(arch["label"]),
            n_clients=int(arch["n_clients"]),
            purchase_interval_months=interval,
            hazard_base=hazard,
            gamme_distribution=gamme_dist,
            switch_prob=switch,
            mean_ticket=float(centroid.get("panier_moyen", 196.0)),
        )
    return result


def _derive_gamme_distribution(part_premium_plus: float) -> dict[str, float]:
    """Derive a 4-gamme probability vector from the premium share centroid."""
    pp = max(0.0, min(1.0, part_premium_plus))
    prestige = pp * 0.3
    premium = pp * 0.7
    remainder = 1.0 - pp
    essentiel = remainder * 0.6
    confort = remainder * 0.4
    return {
        "ESSENTIEL": round(essentiel, 4),
        "CONFORT": round(confort, 4),
        "PREMIUM": round(premium, 4),
        "PRESTIGE": round(prestige, 4),
    }


def load_archetypes_from_json(path: Path | str) -> dict[int, ArchetypeParams]:
    """Convenience: read archetypes.json from disk and parse."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_archetypes_from_payload(payload)
