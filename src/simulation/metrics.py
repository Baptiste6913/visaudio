"""Post-processing of the simulation sales_log into per-step metrics.

P3 Task 5.
"""
from __future__ import annotations

from collections import defaultdict

GAMME_ORDERED: list[str] = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]


def extract_monthly_metrics(sales_log: list[dict], n_steps: int) -> dict:
    """Aggregate the raw sales log into per-step metrics.

    Args:
        sales_log: List of sale dicts, each with keys: step, store, gamme,
            ticket, client_id, archetype_id, conventionnement, age.
        n_steps: Number of simulation steps (1-indexed: steps 1..n_steps).

    Returns:
        Dict with keys:
            ca_reseau: list[float]          -- total CA per step
            ca_par_magasin: dict[str, list[float]]
            mix_gamme_reseau: dict[str, list[float]]  -- share per gamme per step
            panier_moyen: list[float]       -- mean ticket per step
            n_transactions: list[int]       -- count per step
    """
    # Initialize accumulators (0-indexed internally, step i -> index i-1)
    ca_reseau: list[float] = [0.0] * n_steps
    n_transactions: list[int] = [0] * n_steps
    ticket_sums: list[float] = [0.0] * n_steps

    # Per-store CA
    stores_seen: set[str] = set()
    ca_by_store: dict[str, list[float]] = defaultdict(lambda: [0.0] * n_steps)

    # Per-gamme counts for mix
    gamme_counts: dict[str, list[int]] = {g: [0] * n_steps for g in GAMME_ORDERED}

    for sale in sales_log:
        step = sale["step"]
        idx = step - 1  # Convert 1-indexed step to 0-indexed
        if idx < 0 or idx >= n_steps:
            continue

        ticket = sale["ticket"]
        store = sale["store"]
        gamme = sale["gamme"]

        ca_reseau[idx] += ticket
        ticket_sums[idx] += ticket
        n_transactions[idx] += 1

        stores_seen.add(store)
        ca_by_store[store][idx] += ticket

        if gamme in gamme_counts:
            gamme_counts[gamme][idx] += 1

    # Compute panier_moyen (mean ticket per step)
    panier_moyen: list[float] = [
        round(ticket_sums[i] / n_transactions[i], 2) if n_transactions[i] > 0 else 0.0
        for i in range(n_steps)
    ]

    # Round CA
    ca_reseau = [round(v, 2) for v in ca_reseau]

    # Build ca_par_magasin
    ca_par_magasin: dict[str, list[float]] = {
        store: [round(v, 2) for v in ca_by_store[store]]
        for store in sorted(stores_seen)
    }

    # Build mix_gamme_reseau (share per gamme per step)
    mix_gamme_reseau: dict[str, list[float]] = {}
    for g in GAMME_ORDERED:
        shares: list[float] = []
        for i in range(n_steps):
            total = n_transactions[i]
            if total > 0:
                shares.append(round(gamme_counts[g][i] / total, 4))
            else:
                shares.append(0.0)
        mix_gamme_reseau[g] = shares

    return {
        "ca_reseau": ca_reseau,
        "ca_par_magasin": ca_par_magasin,
        "mix_gamme_reseau": mix_gamme_reseau,
        "panier_moyen": panier_moyen,
        "n_transactions": n_transactions,
    }
