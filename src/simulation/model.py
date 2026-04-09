"""VisaudioModel — Mesa 3.5.1 agent-based model for optical retail simulation.

Orchestrates StoreAgents and ClientAgents over a configurable time horizon.
Each simulation step represents one month.

P3 Task 5.
"""
from __future__ import annotations

from typing import Any

import mesa
import pandas as pd

from src.simulation.agents.client import ClientAgent
from src.simulation.agents.store import StoreAgent
from src.simulation.archetypes import load_archetypes_from_payload
from src.simulation.seasonality import compute_seasonality


class VisaudioModel(mesa.Model):
    """Top-level simulation model for the Visaudio optical retail network.

    Args:
        sales_df: Historical sales DataFrame with columns including
            id_client, ville, conventionnement, age_client, date_facture,
            segment_id.
        archetypes_payload: Raw archetypes dict (as loaded from JSON).
        n_steps: Number of simulation steps (months) to run.
        seed: Random seed for reproducibility.
        store_overrides: Optional per-store configuration overrides.
            Maps store_name -> dict with optional keys:
            effort_commercial_level, price_multipliers, active_campaigns.
    """

    def __init__(
        self,
        sales_df: pd.DataFrame,
        archetypes_payload: dict,
        n_steps: int = 36,
        seed: int = 42,
        store_overrides: dict[str, dict[str, Any]] | None = None,
        enable_word_of_mouth: bool = True,
    ) -> None:
        super().__init__(rng=seed)
        self.n_steps: int = n_steps
        self.current_step: int = 0
        self.sales_log: list[dict] = []
        self.enable_word_of_mouth: bool = enable_word_of_mouth

        # Load archetype parameters and seasonality from historical data
        self.archetype_params = load_archetypes_from_payload(archetypes_payload)
        self.seasonality = compute_seasonality(sales_df)

        # Create StoreAgents from unique villes in sales_df
        self.stores: dict[str, StoreAgent] = {}
        store_names = sorted(sales_df["ville"].unique().tolist())
        for name in store_names:
            overrides = (store_overrides or {}).get(name, {})
            store = StoreAgent(
                self,
                store_name=name,
                effort_commercial_level=overrides.get("effort_commercial_level"),
                price_multipliers=overrides.get("price_multipliers"),
                active_campaigns=overrides.get("active_campaigns"),
            )
            self.stores[name] = store

        # Create ClientAgents from historical data
        self._init_clients(sales_df)

        # Build word-of-mouth contact network
        if self.enable_word_of_mouth:
            self._build_contact_network()

    def _init_clients(self, df: pd.DataFrame) -> None:
        """Create one ClientAgent per historical client.

        Groups by id_client to determine:
        - segment_id (first/mode)
        - home store (most frequent ville)
        - conventionnement (most frequent)
        - age (latest age_client)
        - last_purchase_step (negative offset in months before t=0)
        """
        # Reference date = max date in the dataset (t=0 boundary)
        ref_date = df["date_facture"].max()

        grouped = df.groupby("id_client")
        for client_id, group in grouped:
            # Segment / archetype
            segment_id = int(group["segment_id"].mode().iloc[0])
            if segment_id not in self.archetype_params:
                continue  # Skip clients with unknown archetype

            archetype = self.archetype_params[segment_id]

            # Most frequent store
            home_store_name = str(group["ville"].mode().iloc[0])
            if home_store_name not in self.stores:
                continue  # Skip if store not in the model

            # Most frequent conventionnement
            conventionnement = str(group["conventionnement"].mode().iloc[0])

            # Latest age
            last_row = group.sort_values("date_facture").iloc[-1]
            age = int(last_row["age_client"])

            # Last purchase date -> negative step offset (months before t=0)
            last_date = group["date_facture"].max()
            months_diff = (
                (ref_date.year - last_date.year) * 12
                + (ref_date.month - last_date.month)
            )
            last_purchase_step = -months_diff

            ClientAgent(
                self,
                archetype=archetype,
                home_store_name=home_store_name,
                conventionnement=conventionnement,
                age=age,
                last_purchase_step=last_purchase_step,
            )

    def _build_contact_network(self) -> None:
        """Assign 3-5 contacts per client (same store, age ±10 years).

        Simple list-based approach — no NetworkGrid. Each client gets a
        random sample of eligible neighbours from their home store.
        """
        from collections import defaultdict

        # Group clients by home store
        clients_by_store: dict[str, list[ClientAgent]] = defaultdict(list)
        for agent in self.agents_by_type[ClientAgent]:
            clients_by_store[agent.home_store_name].append(agent)

        for store_name, clients in clients_by_store.items():
            for client in clients:
                # Eligible contacts: same store, age within ±10, not self
                eligible = [
                    c for c in clients
                    if c is not client and abs(c.age - client.age) <= 10
                ]
                n_contacts = min(self.random.randint(3, 5), len(eligible))
                if n_contacts > 0:
                    client.contacts = self.random.sample(eligible, n_contacts)

    def step(self) -> None:
        """Advance the simulation by one month.

        Increments current_step and activates all ClientAgents in random
        order (StoreAgents are passive and not stepped).
        """
        self.current_step += 1
        self.agents_by_type[ClientAgent].shuffle_do("step")
