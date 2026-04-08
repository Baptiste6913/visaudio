"""Pydantic schema for a normalized Visaudio sale row.

Each row represents one line of an invoice for one article (one frame,
one lens, or one pair of sunglasses). The schema defines the business
contract between the ingestion layer and everything downstream.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


Famille = Literal["OPT_VERRE", "OPT_MONTURE", "OPT_SOLAIRE"]
GammeVisaudio = Literal["ESSENTIEL", "CONFORT", "PREMIUM", "PRESTIGE"]
CategorieGeom = Literal["UNIFOCAL", "MULTIFOCAL"]
Sexe = Literal["Femme", "Homme"]
StatutClient = Literal["Nouveau client", "Renouvellement"]


class NormalizedSaleRow(BaseModel):
    """One normalized row of the sales dataset."""

    model_config = ConfigDict(extra="forbid")

    ville: str
    implantation: str
    secteur_economique: str
    date_facture: datetime
    id_facture_rang: str = Field(min_length=1)
    rang_paire: int = Field(ge=1)
    famille_article: Famille
    categorie_geom_verre: Optional[CategorieGeom] = None
    gamme_verre_fournisseur: Optional[str] = None
    gamme_verre_visaudio: Optional[GammeVisaudio] = None
    nom_marque: str
    libelle_produit: str
    qte_article: int = Field(gt=0)
    ca_ht_article: float = Field(ge=0)
    id_client: int
    conventionnement: str
    date_naissance_client: Optional[datetime] = None
    sexe: Sexe
    statut_client: Optional[StatutClient] = None

    @model_validator(mode="after")
    def _gamme_visaudio_only_on_verre(self) -> "NormalizedSaleRow":
        if self.famille_article != "OPT_VERRE" and self.gamme_verre_visaudio is not None:
            raise ValueError(
                "gamme_verre_visaudio must be None when famille_article != 'OPT_VERRE'"
            )
        return self
