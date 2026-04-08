"""Normalize a raw Visaudio DataFrame and write it as Parquet.

Takes the output of `read_visaudio_excel` (columns already renamed to
snake_case but dtypes still loose) and produces:
  - a typed DataFrame with derived columns
  - an optional rejected-rows DataFrame listing rows that failed validation
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.api.types import CategoricalDtype
from pydantic import ValidationError

from src.ingestion.schemas import NormalizedSaleRow


GAMME_ORDER = ["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]

AGE_BINS = [0, 30, 45, 60, 75, 200]
AGE_LABELS = ["<30", "30-45", "45-60", "60-75", "75+"]


def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Cast raw columns to their target dtypes (no derived columns yet)."""
    df = df.copy()

    # Categoricals (unordered by default)
    for col in [
        "ville",
        "implantation",
        "secteur_economique",
        "famille_article",
        "categorie_geom_verre",
        "nom_marque",
        "conventionnement",
        "sexe",
        "statut_client",
    ]:
        df[col] = df[col].astype("category")

    # Ordered categorical for the Visaudio gamme
    df["gamme_verre_visaudio"] = df["gamme_verre_visaudio"].astype(
        CategoricalDtype(categories=GAMME_ORDER, ordered=True)
    )

    # Dates (force ns precision per spec §4.1; pandas 3.0 defaults to us)
    df["date_facture"] = pd.to_datetime(df["date_facture"]).astype("datetime64[ns]")
    df["date_naissance_client"] = pd.to_datetime(
        df["date_naissance_client"], errors="coerce"
    ).astype("datetime64[ns]")

    # Numeric
    df["rang_paire"] = df["rang_paire"].astype("int16")
    df["qte_article"] = df["qte_article"].astype("int16")
    df["ca_ht_article"] = df["ca_ht_article"].astype("float64")
    df["id_client"] = df["id_client"].astype("int64")

    # Strings kept as object
    df["id_facture_rang"] = df["id_facture_rang"].astype("string")
    df["gamme_verre_fournisseur"] = df["gamme_verre_fournisseur"].astype("string")
    df["libelle_produit"] = df["libelle_produit"].astype("string")

    return df


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    age_days = (df["date_facture"] - df["date_naissance_client"]).dt.days
    df["age_client"] = (age_days // 365).astype("Int16")
    df["tranche_age"] = pd.cut(
        df["age_client"].astype("float"),
        bins=AGE_BINS,
        labels=AGE_LABELS,
        right=False,
    ).astype("category")
    df["mois_facture"] = df["date_facture"].dt.to_period("M").astype("string")
    df["annee_facture"] = df["date_facture"].dt.year.astype("int16")
    df["est_verre"] = (df["famille_article"] == "OPT_VERRE").astype("bool")
    df["est_premium_plus"] = (
        df["gamme_verre_visaudio"].isin(["PREMIUM", "PRESTIGE"])
    ).astype("bool")
    return df


def _format_validation_error(exc: ValidationError) -> str:
    """Format the first pydantic error into a compact `field: message` string.

    For field-level errors, loc contains the field path. For model_validator
    errors, loc is empty — in that case we strip the "Value error, " prefix
    that pydantic adds and return the raw msg (which typically names the
    offending field explicitly).
    """
    first_err = exc.errors()[0]
    loc = first_err.get("loc", ())
    msg = first_err.get("msg", "")
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]
    if loc:
        field = ".".join(str(p) for p in loc)
        return f"{field}: {msg}"
    return msg


def _validate_rows_pydantic(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate every row against NormalizedSaleRow. Returns (valid, rejected)."""
    valid_mask: list[bool] = []
    reasons: list[str] = []
    records = df.to_dict(orient="records")
    for rec in records:
        try:
            # pydantic does not like pd.NaT — convert to None for optional dates
            clean = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
            NormalizedSaleRow.model_validate(clean)
            valid_mask.append(True)
            reasons.append("")
        except ValidationError as exc:
            valid_mask.append(False)
            reasons.append(_format_validation_error(exc))

    valid = df[valid_mask].reset_index(drop=True)
    rejected = df[[not v for v in valid_mask]].copy().reset_index(drop=True)
    rejected["reason"] = [r for r, ok in zip(reasons, valid_mask) if not ok]
    return valid, rejected


def normalize_dataframe(
    raw: pd.DataFrame, return_rejected: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize a raw DataFrame and (optionally) return rejected rows.

    Args:
        raw: output of `read_visaudio_excel` (columns in snake_case, loose dtypes).
        return_rejected: if True, returns a tuple (valid, rejected).

    Returns:
        A typed DataFrame with derived columns, or a tuple (valid, rejected).
    """
    # First coerce dtypes so the validator sees clean types
    typed = _coerce_dtypes(raw)
    valid, rejected = _validate_rows_pydantic(typed)
    valid = _add_derived_columns(valid)
    if return_rejected:
        return valid, rejected
    return valid


def write_parquet(df: pd.DataFrame, path: Path | str) -> None:
    """Write the normalized DataFrame as Parquet (pyarrow engine)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", index=False)
