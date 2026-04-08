"""KPI pipeline orchestrator — loads the Parquet and produces kpis.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.kpi import (
    benchmark,
    cadrage,
    conventionnement,
    hero,
    retention,
    signals,
)


def _build_meta(df: pd.DataFrame) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(df)),
        "n_clients": int(df["id_client"].nunique()) if len(df) else 0,
        "data_period": {
            "start": str(df["date_facture"].min().date()) if len(df) else None,
            "end": str(df["date_facture"].max().date()) if len(df) else None,
        },
        "annees_data": float(
            max(
                (df["date_facture"].max() - df["date_facture"].min()).days / 365.0,
                0.0,
            )
        )
        if len(df)
        else 0.0,
    }


def _build_hero(df: pd.DataFrame) -> dict:
    h5 = hero.compute_opportunite_upsell(df, segment_col="tranche_age")
    return {
        "opportunite_upsell_annuelle": h5["total_eur_per_year"],
        "opportunite_par_magasin": h5["by_store"],
        "opportunite_par_segment": [
            {"segment": k, "opportunite": v} for k, v in h5["by_segment"].items()
        ],
        "mix_gamme_par_magasin": hero.mix_gamme_par_magasin(df),
        "mix_premium_plus_par_magasin": hero.part_premium_plus_par_magasin(df),
        "ecart_au_top_du_reseau": hero.ecart_au_top_du_reseau(df),
        "taux_cross_sell_verre_monture": hero.taux_cross_sell_verre_monture(df),
        "taux_upgrade_renouvellement": hero.taux_upgrade_renouvellement(df),
    }


def _build_cadrage(df: pd.DataFrame) -> dict:
    # Key names follow spec §5.4 ("par_famille", "par_magasin", "par_mois" as list)
    return {
        "ca_total": cadrage.ca_total(df),
        "par_famille": cadrage.ca_par_famille(df),
        "par_magasin": cadrage.ca_par_magasin(df),
        "panier_moyen": cadrage.panier_moyen_reseau(df),
        "panier_moyen_par_magasin": cadrage.panier_moyen_par_magasin(df),
        "clients_uniques": cadrage.clients_uniques(df),
        "taux_nouveaux_vs_renouv": cadrage.taux_nouveaux_vs_renouv(df),
        "par_mois": [
            {"mois": k, "ca": v} for k, v in cadrage.ca_par_mois(df).items()
        ],
    }


def _build_retention(df: pd.DataFrame) -> dict:
    return {
        "taux_renouvellement_24mois": retention.taux_renouvellement_24mois(df),
        "delai_median_entre_achats_jours": retention.delai_median_entre_achats(df),
        "ltv_3_ans": retention.ltv_3_ans(df),
        "clients_dormants_24mois": retention.clients_dormants(df, 24),
        "cohort_retention_curve": retention.cohort_retention_curve(df),
    }


def _build_benchmark(df: pd.DataFrame) -> dict:
    return {
        "classement_magasins": benchmark.classement_magasins(df),
        "decomposition_ca": benchmark.decomposition_ca(df),
        "ecart_mediane_reseau_ca": benchmark.ecart_mediane_reseau(
            df, metric="ca_par_magasin"
        ),
    }


def _build_conventionnement(df: pd.DataFrame) -> dict:
    return {
        "part_ca_par_conv": conventionnement.part_ca_par_conv(df),
        "panier_moyen_par_conv": conventionnement.panier_moyen_par_conv(df),
        "hhi": conventionnement.hhi_conventionnement(df),
        "exposition_top3": conventionnement.exposition_top3(df),
    }


def _build_signals(df: pd.DataFrame) -> dict:
    return {
        "index_saisonnalite": signals.index_saisonnalite_par_magasin(df),
        "part_clients_60_plus": signals.part_clients_60_plus(df),
        "ratio_monture_verre_eur": signals.ratio_monture_verre_eur(df),
        "ecart_type_mix_intra_magasin": signals.ecart_type_mix_intra_magasin(df),
        "part_factures_une_paire": signals.part_factures_une_paire(df),
    }


def build_kpis_payload(df: pd.DataFrame) -> dict:
    """Assemble the full KPI payload matching spec §5.4."""
    return {
        "meta": _build_meta(df),
        "cadrage": _build_cadrage(df),
        "hero": _build_hero(df),
        "retention": _build_retention(df),
        "benchmark": _build_benchmark(df),
        "conventionnement": _build_conventionnement(df),
        "diagnostic_signals": _build_signals(df),
    }


def write_kpis_json(df: pd.DataFrame, path: Path | str) -> None:
    """Build the payload and write it to `path` as JSON (UTF-8, indent 2)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_kpis_payload(df)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
