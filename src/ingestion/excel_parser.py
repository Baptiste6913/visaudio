"""Read the raw Visaudio Excel file and rename columns to snake_case.

Uses positional renaming (not header-based) to bypass any encoding quirks
in the source header row on Windows.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS: tuple[str, ...] = (
    "ville",
    "implantation",
    "secteur_economique",
    "date_facture",
    "id_facture_rang",
    "rang_paire",
    "famille_article",
    "categorie_geom_verre",
    "gamme_verre_fournisseur",
    "gamme_verre_visaudio",
    "nom_marque",
    "libelle_produit",
    "qte_article",
    "ca_ht_article",
    "id_client",
    "conventionnement",
    "date_naissance_client",
    "sexe",
    "statut_client",
)


def read_visaudio_excel(path: Path | str, sheet_name: str | int = 0) -> pd.DataFrame:
    """Read the raw Visaudio Excel file into a DataFrame with snake_case columns.

    Args:
        path: path to the .xlsx file.
        sheet_name: sheet index or name. Defaults to the first sheet.

    Returns:
        A DataFrame with 19 columns in the order defined by EXPECTED_COLUMNS.
        Column dtypes are those inferred by pandas — NO type coercion here.
        Type coercion and validation happen in src/ingestion/normalization.py.

    Raises:
        FileNotFoundError: if `path` does not exist.
        ValueError: if the sheet has != 19 columns.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path, sheet_name=sheet_name)

    if len(df.columns) != len(EXPECTED_COLUMNS):
        raise ValueError(
            f"Expected 19 columns, got {len(df.columns)} in {path}"
        )

    df.columns = list(EXPECTED_COLUMNS)
    return df
