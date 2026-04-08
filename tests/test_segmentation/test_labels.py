import pandas as pd
import pytest

from src.segmentation.labels import (
    label_archetype_from_centroid,
    sort_and_label_archetypes,
)


def test_label_high_age_libre_premium():
    centroid = pd.Series(
        {
            "age_dernier_achat": 65.0,
            "panier_moyen": 280.0,
            "n_achats_totaux": 2.5,
            "mois_entre_achats": 22.0,
            "part_premium_plus": 0.75,
            "ratio_monture_verre": 0.35,
            "conventionnement_libre": 0.85,
            "sexe_Femme": 0.6,
            "sexe_Homme": 0.4,
        }
    )
    label = label_archetype_from_centroid(centroid)
    assert "60-75" in label or "60+" in label
    assert "LIBRE" in label


def test_label_young_css_essentiel():
    centroid = pd.Series(
        {
            "age_dernier_achat": 25.0,
            "panier_moyen": 95.0,
            "n_achats_totaux": 1.0,
            "mois_entre_achats": 0.0,
            "part_premium_plus": 0.0,
            "ratio_monture_verre": 0.0,
            "conventionnement_libre": 0.1,
            "sexe_Femme": 0.4,
            "sexe_Homme": 0.6,
        }
    )
    label = label_archetype_from_centroid(centroid)
    assert "<30" in label or "30" in label
    assert "NON-LIBRE" in label or "CSS" in label or "réseau" in label.lower()


def test_sort_orders_by_panier_moyen_descending():
    centroids = pd.DataFrame(
        [
            # Cluster 0 — low panier
            {"age_dernier_achat": 30, "panier_moyen": 100, "n_achats_totaux": 1,
             "mois_entre_achats": 0, "part_premium_plus": 0, "ratio_monture_verre": 0,
             "conventionnement_libre": 0.5, "sexe_Femme": 0.5, "sexe_Homme": 0.5},
            # Cluster 1 — high panier
            {"age_dernier_achat": 65, "panier_moyen": 300, "n_achats_totaux": 3,
             "mois_entre_achats": 20, "part_premium_plus": 0.8, "ratio_monture_verre": 0.3,
             "conventionnement_libre": 0.9, "sexe_Femme": 0.5, "sexe_Homme": 0.5},
            # Cluster 2 — mid panier
            {"age_dernier_achat": 50, "panier_moyen": 200, "n_achats_totaux": 2,
             "mois_entre_achats": 18, "part_premium_plus": 0.4, "ratio_monture_verre": 0.25,
             "conventionnement_libre": 0.7, "sexe_Femme": 0.5, "sexe_Homme": 0.5},
        ]
    )
    ordered = sort_and_label_archetypes(centroids)
    # New id 0 should correspond to the HIGHEST panier_moyen (old cluster 1)
    assert ordered.iloc[0]["panier_moyen"] == 300
    assert ordered.iloc[1]["panier_moyen"] == 200
    assert ordered.iloc[2]["panier_moyen"] == 100
    # original_cluster_id tracks the mapping from new id back to sklearn's id
    assert ordered.iloc[0]["original_cluster_id"] == 1
    assert ordered.iloc[2]["original_cluster_id"] == 0
    # Each row has a label
    assert all(isinstance(l, str) and len(l) > 0 for l in ordered["label"])
