# Architecture Spec — Visaudio Optique Analytics

**Statut :** validé (brainstorming 2026-04-08)
**Auteur :** Baptiste Bouault (via session brainstorming Claude Code)
**Périmètre :** Phase 1 — outil d'analyse et de simulation pour le réseau Visaudio Optique (6 magasins Normandie).

---

## 1. Résumé exécutif

Visaudio Optique Analytics est un outil local (zéro dépendance cloud en Phase 1) qui transforme un fichier Excel descriptif (~80 K lignes de factures optique 2023-2025) en un dashboard interactif multi-rôle, pour répondre à la question business centrale :

> **« Comment grandir sans ouvrir de magasin ? »**

Le livrable Phase 1 doit **impressionner le comex Visaudio** pour ouvrir la porte à une Phase 2 payante (branchement API temps réel, ML, services récurrents). L'audience démo = membre(s) du comex en charge de la data (donc data-literate, exigeants sur la méthodo).

Le hero du pitch est un chiffre statique **défendable** ("vous laissez ~800 K€/an sur la table en upsell verre") dérivé d'une analyse segmentée des données, complété par une **simulation Mesa interactive** qui montre la dynamique temporelle d'adoption des interventions.

---

## 2. Décisions structurantes (validées)

| # | Décision | Justification |
|---|---|---|
| **D1** | Dashboard multi-rôle (Direction réseau + Manager magasin) avec switch de vue | Même code, deux cas d'usage servis |
| **D2** | Hero narrative = upsell / croissance sans ouvrir | Pitch clair, défendable, aligné sur les leviers réels du DG |
| **D3** | Approche hybride : stat segmentée (hero) + Mesa (dynamique) | Chiffre indiscutable + wow moment de la simulation |
| **D4** | Leviers retenus : **L2 effort commercial (hero)**, L1 pricing, L4 ciblage, L5 conventionnement (défensif). L3 mix produit exclu. | L3 est structurel, pas un levier à 18 mois |
| **D5** | Architecture **Approche C** : KPIs pré-calculés en JSON statique + FastAPI dédié aux scénarios Mesa | Maximise wow/effort, prépare Phase 2 |
| **D6** | Client `api.ts` unifié côté React qui cache l'origine des données (JSON statique vs API) | Un seul point d'accès pour les composants |
| **D7** | **Pré-chauffage Mesa** au démarrage du backend sur les 3-5 scénarios clés | Pas de latence de 30s pendant la démo |
| **D8** | StoreAgent **passif** en Phase 1 (tient les paramètres et enregistre, pas de logique d'optimisation locale) | Over-engineering Phase 2 |
| **D9** | **Plan B calibration** : si le modèle Mesa ne converge pas aux tolérances, on bascule en "projection qualitative" et H5 porte le pitch tout seul | La livraison ne doit pas être bloquée par la calibration |
| **D10** | 6 scénarios pré-chauffés : BASE + L2a (hero) + L2b + L1a + L4a + L5a | Couvre le hero et les variantes clés sans exploser le démarrage |
| **D11** | 30 KPIs au total, dont ~8 consommés directement par le dashboard (le reste = intermédiaires ou drill-downs) | Périmètre complet sans surinflation |
| **D12** | Formule hero H5 = **écart de panier moyen au top-quartile du segment × volume de ventes** (défendable : "c'est dans vos propres données") | Évite les projections pour le chiffre hero |

---

## 3. Architecture globale

### 3.1 Vue d'ensemble — Approche C

```
┌─────────────┐
│Excel source │  data/raw/modele_donnees_optique.xlsx
└──────┬──────┘
       │ (une fois)
       ▼
┌─────────────┐
│ Ingestion   │  pandas + pydantic — src/ingestion/
└──────┬──────┘
       ▼
┌─────────────┐
│ Parquet     │  data/processed/sales.parquet  (source de vérité typée)
└──────┬──────┘
       │
       ├───────────────┬─────────────────────┐
       ▼               ▼                     ▼
┌─────────────┐ ┌─────────────┐       ┌─────────────┐
│ KPI engine  │ │Segmentation │       │ Calibration │
│ (batch pur) │ │  K-Means    │──────▶│    Mesa     │
└──────┬──────┘ └──────┬──────┘       └──────┬──────┘
       │               │                     │
       ▼               ▼                     ▼
┌─────────────┐ ┌─────────────┐       ┌────────────────┐
│ kpis.json   │ │archetypes   │       │mesa_runs/      │
│ (statique)  │ │.json        │       │(pré-warm 6 sc.)│
└──────┬──────┘ └──────┬──────┘       └────────┬───────┘
       │               │                       │
       └───────────────┴──────────┬────────────┘
                                  ▼
                       ┌────────────────────┐
                       │ FastAPI backend    │
                       │ GET /kpis          │
                       │ GET /archetypes    │
                       │ POST /simulate     │
                       └─────────┬──────────┘
                                 ▼
                       ┌────────────────────┐
                       │ React Dashboard    │
                       │ (api.ts unifié)    │
                       └────────────────────┘
```

### 3.2 Contrats entre couches

| De → vers | Format | Fraîcheur |
|---|---|---|
| Excel → Parquet | `sales.parquet` (pyarrow) | Regénéré sur commande CLI |
| Parquet → JSON KPIs | `kpis.json` (schéma doc §6.3) | Regénéré sur commande CLI |
| Parquet → archétypes | `archetypes.json` (schéma doc §7.3) | Regénéré sur commande CLI |
| Parquet → runs Mesa | `mesa_runs/<scenario_hash>.json` | Généré au démarrage du backend |
| Backend → Front | JSON via HTTP (FastAPI) | Temps réel pour `/simulate`, statique pour `/kpis` et `/archetypes` |

---

## 4. Modèle de données

### 4.1 Schéma du Parquet normalisé `sales.parquet`

Les 19 colonnes brutes de l'Excel sont normalisées comme suit :

| Colonne normalisée | dtype | Source | Transformation |
|---|---|---|---|
| `ville` | `category` | `Ville` | strip + title case |
| `implantation` | `category` | `Implantation` | upper + strip |
| `secteur_economique` | `category` | `Secteur économique` | — |
| `date_facture` | `datetime64[ns]` | `datefacture` | parse |
| `id_facture_rang` | `string` | `id Facture rang` | — |
| `rang_paire` | `int16` | `Rang paire` | — |
| `famille_article` | `category` | `Famille Article` | upper |
| `categorie_geom_verre` | `category` | `Catégorie géométrie verre` | nullable |
| `gamme_verre_fournisseur` | `string` | `Gamme verre fournisseur` | nullable |
| `gamme_verre_visaudio` | `category` | `Gamme verre Visaudio` | nullable, ordered: ESSENTIEL < CONFORT < PREMIUM < PRESTIGE |
| `nom_marque` | `category` | `nommarque` | — |
| `libelle_produit` | `string` | `libelle produit` | — |
| `qte_article` | `int16` | `Qte article` | — |
| `ca_ht_article` | `float64` | `CA HT article` | — |
| `id_client` | `int64` | `id Client` | — |
| `conventionnement` | `category` | `Conventionnement` | upper + strip |
| `date_naissance_client` | `datetime64[ns]` | `datenaissance client` | nullable |
| `sexe` | `category` | `Sexe` | — |
| `statut_client` | `category` | `Nouveau client / Renouvellement` | nullable |

### 4.2 Règles métier encodées (pydantic)

Au niveau pydantic (`src/ingestion/schemas.py`), on force :

- `gamme_verre_visaudio IS NULL WHEN famille_article != 'OPT_VERRE'` (règle métier : la gamme ne s'applique qu'aux verres)
- `qte_article > 0`
- `ca_ht_article >= 0`
- `rang_paire >= 1`
- `id_facture_rang` ne doit pas être vide

Ces règles produisent un **rejection log** `data/processed/rejected_rows.json` avec la raison du rejet.

### 4.3 Colonnes dérivées ajoutées au Parquet

| Colonne | Type | Calcul |
|---|---|---|
| `age_client` | `int16` | `(date_facture - date_naissance_client).dt.days // 365` |
| `tranche_age` | `category` | binning : `<30`, `30-45`, `45-60`, `60-75`, `75+` |
| `mois_facture` | `period[M]` | `date_facture.dt.to_period('M')` |
| `annee_facture` | `int16` | |
| `est_verre` | `bool` | `famille_article == 'OPT_VERRE'` |
| `est_premium_plus` | `bool` | `gamme_verre_visaudio in ('PREMIUM', 'PRESTIGE')` |

---

## 5. KPI engine

### 5.1 Principes d'architecture

- **Chaque KPI = une fonction pure** `def kpi_XX(df: pd.DataFrame, **params) -> <return_type>` dans `src/kpi/`.
- **Aucun I/O dans ces fonctions** (pas de lecture Parquet, pas d'écriture JSON). L'I/O est dans un orchestrateur `src/kpi/pipeline.py`.
- Testable en isolation avec un DataFrame forgé à la main (5-10 lignes).
- Le résultat final est sérialisé en JSON avec une structure pivotable par le front.

### 5.2 Liste exhaustive des KPIs (30)

Notations : `fa` = `famille_article`, `fid` = `id_facture_rang`, `cid` = `id_client`, `gv` = `gamme_verre_visaudio`, `conv` = `conventionnement`.

#### Groupe 1 — Cadrage (top-line)

| ID | KPI | Formule |
|---|---|---|
| **C1** | CA total HT | `df["ca_ht_article"].sum()` |
| **C2** | CA par famille | `df.groupby("fa")["ca_ht_article"].sum()` |
| **C3** | CA par magasin | `df.groupby("ville")["ca_ht_article"].sum()` |
| **C4** | Panier moyen facture (réseau) | `df.groupby("fid")["ca_ht_article"].sum().mean()` |
| **C5** | Panier moyen facture par magasin | `df.groupby(["ville","fid"])["ca_ht_article"].sum().groupby("ville").mean()` |
| **C6** | Clients uniques (réseau + par magasin) | `df["cid"].nunique()` et `df.groupby("ville")["cid"].nunique()` |
| **C7** | Taux nouveaux vs renouvellement | `df.drop_duplicates("cid").groupby("statut_client").size()` normalisé |
| **C8** | CA par mois (série temporelle) | `df.set_index("date_facture").resample("MS")["ca_ht_article"].sum()` |

#### Groupe 2 — HERO upsell / croissance

| ID | KPI | Formule |
|---|---|---|
| **H1** | Mix gamme verre par magasin | Sur `est_verre` : `groupby(["ville","gv"])["ca_ht_article"].sum() / groupby("ville")["ca_ht_article"].sum()` → matrice ville × gamme en % |
| **H2** | Mix gamme verre par segment client | Idem H1 mais `groupby(["segment","gv"])` |
| **H3** | Panier moyen verre par segment | `df[est_verre].groupby("segment")["ca_ht_article"].mean()` |
| **H4** | Panier moyen verre par segment × magasin, puis Q75 par segment | `panier_q75[s] = df[est_verre].groupby(["segment","ville"])["ca_ht_article"].mean().groupby("segment").quantile(0.75)` |
| **H5** | **Opportunité upsell €/an (HERO)** | Voir §5.3 |
| **H6** | Opportunité upsell par magasin | H5 restreint à un magasin : gap du magasin vs son top-quartile segment |
| **H7** | Taux de cross-sell verre+monture | `% factures contenant (est_verre ET famille_article=='OPT_MONTURE')` sur total factures verre |
| **H8** | Taux d'upgrade au renouvellement | Pour chaque `cid` en renouvellement : gamme paire `rang_paire=1` dernière facture vs avant — `% qui monte en gamme` |
| **H9** | Part PREMIUM+PRESTIGE par magasin | `df[est_verre].groupby("ville")["est_premium_plus"].mean()` — la métrique la plus lisible du hero |
| **H10** | Écart du magasin au top du réseau | `H9[mag] - H9.max()` — négatif = sous-performance |

#### Groupe 3 — Secondaires

**Rétention / LTV**

| ID | KPI | Formule |
|---|---|---|
| **R1** | Taux de renouvellement 24 mois | `% clients avec ≥2 factures à <24 mois d'écart / clients avec ≥24 mois d'historique` |
| **R2** | Délai médian entre achats | Par client : `median(diff(date_facture))` sur clients avec ≥2 achats |
| **R3** | LTV 3 ans | `df.groupby("cid")["ca_ht_article"].sum()` restreint aux clients avec ≥3 ans d'historique |
| **R4** | Clients dormants (>24 mois) | `count(cid WHERE max(date_facture) < today - 24mois)` |
| **R5** | Cohort retention curve | Par cohorte de premier achat (mois), % actif à M+6, M+12, M+24 |

**Benchmark inter-magasins**

| ID | KPI | Formule |
|---|---|---|
| **B1** | Classement magasin par CA | `df.groupby("ville")["ca_ht_article"].sum().rank(ascending=False)` |
| **B2** | Décomposition CA = n_factures × panier_moyen | Waterfall par magasin |
| **B3** | Écart à la médiane réseau | Pour chaque KPI : `(kpi_mag - median_reseau) / median_reseau` |
| **B4** | Best practice importée (contrefactuel) | "Si mag X adopte le mix de mag Y, ΔCA = ?" — pondération |

**Dépendance conventionnement**

| ID | KPI | Formule |
|---|---|---|
| **D1** | % CA par conventionnement | `df.groupby("conv")["ca_ht_article"].sum() / total` |
| **D2** | Panier moyen par conventionnement | `df.groupby(["conv","fid"])["ca_ht_article"].sum().groupby("conv").mean()` |
| **D3** | HHI concentration | `sum((part_i)**2)` sur les conventionnements (>2500 = très concentré) |
| **D4** | Top-3 exposition | `% CA venant des 3 plus gros conventionnements` |

#### Groupe 4 — Signaux diagnostic (alimente le moteur de règles)

| ID | KPI | Usage |
|---|---|---|
| **X1** | Index saisonnalité mensuel par magasin | Alerte si profil atypique |
| **X2** | Part clients 60+ | Alerte si >40 % → portefeuille vieillissant |
| **X3** | Ratio Monture/Verre € | Alerte si <0.25 → sous-attachement monture |
| **X4** | Écart-type intra-magasin du mix gamme | Alerte si trop élevé → manque de consistance |
| **X5** | % factures à 1 seule paire | Alerte si >80 % → manque de 2e paire |

### 5.3 La formule HERO en détail — H5

**Définition mathématique** :

Soit `S` l'ensemble des segments client (clusters K-Means), `V` l'ensemble des magasins. Pour chaque segment `s ∈ S` :

```
panier_actuel(s)    = mean(ca_ht_article | est_verre, segment = s)
panier_top_q75(s)   = quantile_0.75 over V of
                        mean(ca_ht_article | est_verre, segment = s, ville = v)
gap(s)              = max(0, panier_top_q75(s) - panier_actuel(s))
n_ventes_verre(s)   = count(rows | est_verre, segment = s)
opportunite(s)      = gap(s) * n_ventes_verre(s)

TOTAL_OPPORTUNITE   = sum over s of opportunite(s) / annees_data
```

**Propriétés** :
- Le `max(0, ...)` garantit qu'un segment au-dessus du top-quartile n'est pas compté négativement
- `annees_data` est calculé sur la plage `[min(date_facture), max(date_facture)]`
- Le chiffre est **défendable** : c'est uniquement de l'arithmétique sur les données historiques, aucune projection

**Unité affichée** : K€/an (arrondi à 10 K€ près).

**Variante par magasin (H6)** :
```
opp_mag(v) = sum over s of max(0, panier_top_q75(s) - panier_mag_segment(v, s))
             * n_ventes_verre_mag_segment(v, s)
             / annees_data
```

### 5.4 Structure JSON produit par le pipeline KPI

Le fichier `data/processed/kpis.json` a une structure **pivotable** par le front :

```json
{
  "meta": {
    "generated_at": "2026-04-08T11:30:00Z",
    "data_period": { "start": "2023-01-01", "end": "2025-12-31" },
    "n_rows": 79200,
    "n_clients": 21340,
    "annees_data": 3.0
  },
  "cadrage": {
    "ca_total": 9100000,
    "panier_moyen": 196,
    "clients_uniques": 21340,
    "par_famille": { "OPT_VERRE": 7100000, "OPT_MONTURE": 1820000, "OPT_SOLAIRE": 180000 },
    "par_magasin": { "Avranches": 1300000, "Carentan-les-Marais": ... },
    "par_mois": [ { "mois": "2023-01", "ca": 210000 }, ... ]
  },
  "hero": {
    "opportunite_upsell_annuelle": 820000,
    "opportunite_par_magasin": { "Avranches": 142000, ... },
    "opportunite_par_segment": [
      { "segment_id": 3, "segment_label": "50-65 CSP+", "opportunite": 340000 },
      ...
    ],
    "mix_premium_plus_par_magasin": { "Avranches": 0.18, "Carentan-les-Marais": 0.32, ... }
  },
  "retention": { ... },
  "benchmark": { ... },
  "conventionnement": { ... },
  "diagnostic_signals": { ... }
}
```

---

## 6. Segmentation clients (K-Means)

### 6.1 Features de clustering

Par client (`cid`), on agrège l'historique pour produire un vecteur de features :

| Feature | Calcul | Notes |
|---|---|---|
| `age_dernier_achat` | âge lors de la dernière facture | normalisé |
| `sexe` | one-hot | |
| `panier_moyen` | `mean(ca_ht_article)` sur ses lignes | standardisé |
| `n_achats_totaux` | `nunique(fid)` | log-normalisé |
| `mois_entre_achats` | `median(diff(date_facture))` | pour clients >1 achat |
| `part_premium_plus` | `mean(est_premium_plus)` sur ses lignes verre | |
| `ratio_monture_verre` | `sum(CA si monture) / sum(CA si verre)` | |
| `conventionnement_libre` | `mean(conv == 'LIBRE')` | proxy CSP |
| `conventionnement_top3` | `mean(conv ∈ top3_réseau)` | |

### 6.2 Procédure

1. Standardiser les features (`StandardScaler`)
2. Choisir `k` par méthode du coude + silhouette — viser `k ∈ [6, 10]`
3. Labelliser les clusters avec des noms humains interprétables (ex: "50-65 CSP+", "Jeunes adultes renouvellement rapide", "Seniors 75+")
4. Stocker le centroide et la label dans `archetypes.json`
5. Joindre le cluster au DataFrame principal pour tous les KPIs downstream

### 6.3 Structure `archetypes.json`

```json
{
  "n_archetypes": 7,
  "archetypes": [
    {
      "id": 0,
      "label": "50-65 CSP+",
      "n_clients": 4820,
      "share_of_clients": 0.226,
      "share_of_ca": 0.312,
      "centroid": {
        "age_dernier_achat": 58.3,
        "panier_moyen": 268,
        "part_premium_plus": 0.42,
        "ratio_monture_verre": 0.31,
        "conventionnement_libre": 0.68
      },
      "description": "Clients actifs, haut de gamme, fortement LIBRE, bon attachement monture"
    },
    ...
  ]
}
```

---

## 7. Moteur de règles (diagnostic)

### 7.1 Principe

Le moteur de règles est **déclaratif**. Chaque règle prend en entrée :
- un `scope` : `"network"` ou `"store"` ou `"segment"`
- une `condition` évaluable sur les KPIs
- un `severity` : `critical` | `warning` | `info`
- un `finding_template` : texte du message, peut interpoler des valeurs KPI
- un optionnel `recommendation` : texte d'action suggérée

Les règles sont stockées dans `src/rules/rules.yaml` pour pouvoir être ajustées sans toucher au code.

### 7.2 Exemples de règles

```yaml
- id: MIX_ESSENTIEL_EXCESS
  scope: store
  severity: warning
  condition: "mix_essentiel > 0.45 AND mix_essentiel > 1.3 * mix_essentiel_network_median"
  finding: "Mix ESSENTIEL surreprésenté ({mix_essentiel:.0%} vs {network:.0%} réseau)"
  recommendation: "Formation upsell prioritaire sur segment CSP+"

- id: CROSS_SELL_MONTURE_LOW
  scope: store
  severity: critical
  condition: "ratio_monture_verre < 0.25"
  finding: "Sous-attachement monture (ratio {ratio:.2f} vs {network:.2f} réseau)"
  recommendation: "Cross-sell monture à l'achat verre — potentiel +{potentiel:.0f} K€/an"

- id: PORTEFEUILLE_VIEILLISSANT
  scope: store
  severity: warning
  condition: "part_clients_60_plus > 0.40"
  finding: "{part:.0%} de clients 60+ — risque de rétention à moyen terme"

- id: CONVENTIONNEMENT_CONCENTRATION
  scope: network
  severity: warning
  condition: "hhi_conventionnement > 2500"
  finding: "Concentration conventionnement élevée (HHI {hhi:.0f}) — risque de dépendance"
```

### 7.3 Output

Pour chaque magasin, un tableau de findings triés par sévérité, sérialisé dans `data/processed/diagnostics.json` :

```json
{
  "Avranches": {
    "findings": [
      { "id": "CROSS_SELL_MONTURE_LOW", "severity": "critical", "message": "...", "recommendation": "..." },
      { "id": "MIX_ESSENTIEL_EXCESS", "severity": "warning", "message": "...", "recommendation": "..." }
    ]
  },
  "Carentan-les-Marais": { ... }
}
```

Consommé par le dashboard à la page drill-down magasin (panneau "Diagnostic auto") via `GET /diagnostics`.

---

## 8. Simulation Mesa

### 8.1 Framework

- **Mesa 3.2+** (`pip install "mesa[rec]"`)
- Référence : `Hotelling's Law`, `El Farol`
- 1 step = 1 mois, horizon standard = 36 mois

### 8.2 ClientAgent

**Attributs** :

| Attribut | Type | Source | Notes |
|---|---|---|---|
| `agent_id` | int | — | unique |
| `archetype_id` | int (0..N-1) | K-Means | 1 des 6-10 clusters |
| `age` | int | `today − date_naissance_client` | vieillit à chaque step |
| `conventionnement` | str | historique (le plus fréquent) | considéré stable |
| `home_store` | str | historique (magasin majoritaire) | peut changer selon scénario |
| `last_purchase_date` | int (step) | état initial depuis historique | |
| `last_purchase_gamme` | str | état | |
| `personal_purchase_interval` | int | archétype ± bruit | fréquence d'achat individuelle |

**Comportement par step** (pseudo-code) :

```python
def step(self):
    months_since = current_step - self.last_purchase_date
    if months_since < self.personal_purchase_interval:
        return

    p_buy = self.archetype.hazard(self.age, self.conv, months_since) \
            * self.model.seasonality[current_month]
    if self.model.random.random() > p_buy:
        return

    store = self.home_store if self.model.random.random() > self.archetype.switch_prob \
            else self.model.random_other_store(self.home_store)

    base_probs = self.archetype.gamme_distribution
    effort = store.effort_commercial_level.get(self.archetype_id, 1.0)
    price = store.price_multipliers
    final_probs = apply_effort_and_price(base_probs, effort, price)
    gamme = sample(final_probs, rng=self.model.random)

    ticket = sample_ticket_for(gamme, self.archetype_id, rng=self.model.random)
    self.model.record_sale(store, self, gamme, ticket, current_step)
    self.last_purchase_date = current_step
    self.last_purchase_gamme = gamme
```

### 8.3 StoreAgent

**Passif en Phase 1.** Il tient les paramètres et enregistre les ventes.

**Attributs** :

| Attribut | Type | Notes |
|---|---|---|
| `store_name` | str | une des 6 villes |
| `effort_commercial_level` | dict[archetype_id → float] | clé du scénario L2. 1.0 = baseline |
| `price_multipliers` | dict[gamme → float] | scénario L1. 1.0 = baseline |
| `active_campaigns` | list[dict] | scénario L4 : `{target_archetype, reactivation_boost, window_months}` |

### 8.4 VisaudioModel

Hérite de `mesa.Model`.

**Attributs globaux** :

| Attribut | Type | Notes |
|---|---|---|
| `seasonality` | dict[int(month) → float] | coefficient multiplicatif, appris sur historique |
| `market_drift` | float | tendance annuelle globale |
| `current_step` | int | mois simulé depuis t=0 |
| `schedule` | `RandomActivation` | sur les ClientAgents uniquement |
| `datacollector` | `mesa.DataCollector` | collecte métriques à chaque step |

**Métriques collectées par step** :
- CA réseau
- CA par magasin
- Mix gamme réseau
- Mix gamme par magasin
- Panier moyen
- Nombre de transactions

### 8.5 Calibration

**Objectif** : reproduire l'historique en agrégat, pas au niveau individuel.

**Tolérances cibles** :

| Métrique | Tolérance |
|---|---|
| CA total annuel par magasin | ±5 % |
| Mix gamme verre par magasin | ±3 pp par gamme |
| Panier moyen par segment | ±10 % |
| Saisonnalité mensuelle (R² du profil) | ≥ 0.8 |

> **Note** : la tolérance sur le panier moyen par segment est volontairement relâchée à ±10 % pour tenir compte des petits échantillons dans les petits magasins (par exemple Coutances ~250 clients). Mieux vaut une cible atteignable qu'un blocage sur la calibration — le plan B reste la garantie de livraison.

**Procédure** :

1. **Train** sur 2023-2024 : initialiser archétypes, dériver distributions, calibrer `personal_purchase_interval`, `switch_prob`, `seasonality[month]`.
2. **Backtest** sur 2025 : lancer la baseline et comparer.
3. **Optimisation manuelle** (pas de grid search) : tuner les paramètres les plus sensibles jusqu'à atteindre les tolérances.
4. **Gel** des paramètres une fois calibré.

**Plan B** (D9) : si le modèle ne converge pas aux tolérances après quelques itérations, on affiche les courbes avec disclaimer "projection qualitative" et on s'appuie principalement sur H5 (statique) pour le pitch. La démo ne doit pas être bloquée par la calibration.

### 8.6 Scénarios

| ID | Nom | Levier | Input | Output |
|---|---|---|---|---|
| **SC-BASE** | Baseline calibré | — | `effort=1.0`, `price=1.0` | trajectoire CA 36 mois |
| **SC-L2a** (HERO) | Effort commercial ciblé | L2 | `effort[archetype_50_65_CSP+] = 1.3` sur les 6 magasins | trajectoire + uplift |
| **SC-L2b** | Best-in-class | L2 | `effort[all] = max_observé` | borne haute théorique |
| **SC-L1a** | Baisse PREMIUM -10% | L1 | `price[PREMIUM] = 0.9` | élasticité observée |
| **SC-L4a** | Campagne dormants | L4 | `campaigns = [{target: dormants, boost: +30%, window: 6}]` | CA incrémental |
| **SC-L5a** | Santéclair -10% rembours. | L5 (défensif) | modifie panier moyen `conv=SANTECLAIR` | CA à risque |

**Pré-chauffage démo** : au démarrage du backend, les 6 scénarios sont calculés (20 réplications × 36 mois chacun) et stockés en cache (clé = `sha256(scenario_name + params_json)`). Estimation : 2-5 min au premier démarrage, ensuite lecture disque instantanée.

### 8.7 Scénario HERO — `SC-L2a` (détail)

**Narration pour le comex** :
> *"Vos opticiens n'ont pas le réflexe de proposer systématiquement PREMIUM aux clients 50-65 CSP+. Un programme de formation ciblé, sans changer les prix ni le catalogue, devrait faire remonter le taux de conversion sur ce segment. Voici la dynamique simulée sur 36 mois."*

**Paramètres** :
- `effort_commercial[archetype_50_65_CSP+] = 1.3` (boost 30 %)
- Appliqué sur les 6 magasins
- 20 réplications Monte Carlo

**Output attendu** :
- Deux courbes CA mensuel (baseline vs intervention) avec bande CI
- Chiffre clé : `ΔCA_cumulé_36mois` avec CI 95 %
- Affiché en page simulation du dashboard

---

## 9. Backend API (FastAPI)

### 9.1 Endpoints

| Méthode | Route | Input | Output | Source |
|---|---|---|---|---|
| GET | `/health` | — | `{ "status": "ok" }` | — |
| GET | `/kpis` | — | contenu de `kpis.json` | fichier statique |
| GET | `/archetypes` | — | contenu de `archetypes.json` | fichier statique |
| GET | `/diagnostics` | — | contenu de `diagnostics.json` (sortie moteur de règles) | fichier statique |
| GET | `/scenarios` | — | liste des scénarios disponibles + leurs params | statique |
| POST | `/simulate` | `{ scenario_id, params }` | `{ trajectories, ci, delta_ca, ...}` | cache-first, Mesa on miss |

### 9.2 Cache Mesa

- Clé : `sha256(scenario_id + json.dumps(params, sort_keys=True))`
- Stockage : `data/processed/mesa_runs/<hash>.json`
- Au démarrage du backend : lancer le pré-chauffage en arrière-plan pour les 6 scénarios standards
- Cache-hit : lecture fichier JSON → instantané
- Cache-miss : lancer Mesa (bloquant, quelques secondes), stocker, retourner

### 9.3 Modèles pydantic

```python
class SimulateRequest(BaseModel):
    scenario_id: Literal["BASE", "L2a", "L2b", "L1a", "L4a", "L5a"]
    params: dict[str, Any] = {}

class Trajectory(BaseModel):
    months: list[int]
    ca_mean: list[float]
    ca_lower: list[float]  # CI 95% lower
    ca_upper: list[float]  # CI 95% upper

class SimulateResponse(BaseModel):
    scenario_id: str
    params: dict
    baseline: Trajectory
    intervention: Trajectory
    delta_ca_cumul_36m: float
    delta_ca_ci_low: float
    delta_ca_ci_high: float
    n_replications: int
    from_cache: bool
```

---

## 10. Dashboard

### 10.1 Structure

```
dashboard/src/
├── components/
│   ├── ui/              # shadcn primitives (Button, Card, Dialog, ...)
│   ├── charts/          # wrappers Recharts (RevenueChart, MixChart, WaterfallChart, CiCurveChart)
│   ├── KpiCard.tsx      # carte KPI réutilisable
│   ├── FindingList.tsx  # liste de findings du moteur de règles
│   └── RoleSwitcher.tsx # switch Direction / Manager
├── hooks/
│   ├── useKpis.ts       # fetch GET /kpis (cached)
│   ├── useArchetypes.ts # fetch GET /archetypes
│   └── useSimulate.ts   # POST /simulate avec état loading
├── pages/
│   ├── LandingPage.tsx          # Page 1
│   ├── StoreDrilldownPage.tsx   # Page 2
│   ├── ScenarioPage.tsx         # Page 3
│   └── SegmentsPage.tsx         # bonus : archétypes
├── utils/
│   ├── api.ts           # client unifié (cache l'origine des données)
│   ├── format.ts        # formatters € / % / dates
│   └── roles.ts         # logique multi-rôle
└── App.tsx              # routes
```

### 10.2 Client API unifié (`utils/api.ts`)

```typescript
// Un seul point d'accès qui cache l'origine JSON statique vs POST FastAPI
export async function getKpis(): Promise<KpisPayload> {
  return fetchJson('/kpis');
}

export async function getArchetypes(): Promise<ArchetypesPayload> {
  return fetchJson('/archetypes');
}

export async function simulate(
  scenarioId: ScenarioId,
  params: SimulateParams
): Promise<SimulateResponse> {
  return fetchJson('/simulate', { method: 'POST', body: JSON.stringify({ scenario_id: scenarioId, params }) });
}
```

### 10.3 Page 1 — Landing (Direction réseau)

**Composants** :
- `<RoleSwitcher />` en header (défaut : Direction)
- `<HeroCard />` : le chiffre H5 en grand (820 K€)
- `<KpiRow />` : 4 `KpiCard` (CA, panier, clients, mix PREMIUM)
- `<Chart title="Opportunité upsell par magasin" variant="bar-horizontal">`
- `<Chart title="Opportunité upsell par segment" variant="bar-horizontal">`
- Navigation : liens vers les 3 autres pages

**Données** : un seul `useKpis()`.

### 10.4 Page 2 — Drill-down magasin

**Composants** :
- Header avec retour + sélecteur magasin + `<RoleSwitcher />`
- `<KpiRow />` : 4 KPI cards avec écart à la médiane (rouge/vert)
- `<Chart title="Opportunité locale par segment" variant="waterfall">`
- `<FindingList storeId={ville} />` : panneau diagnostic auto du moteur de règles
- `<Tabs>` : Mix gamme | Pyramide clients | Saison | Conventionnement
- Pour chaque tab, un Chart adapté

**Données** : `useKpis()` filtré par magasin + `useDiagnostics(magasin)`.

**Accessible en vue Direction** (drill-down depuis la landing) **ou en vue Manager** (page d'atterrissage directe pour les managers).

### 10.5 Page 3 — Simulation (page "wow")

**Composants** :
- Header avec sélecteur de scénario
- Panneau gauche : `<SliderRow />` pour chaque paramètre, `<SegmentSelector />`, `<StoreSelector />`, bouton "Lancer la simulation"
- Panneau droit : `<CiCurveChart />` (deux courbes avec bande CI), `<ResultBox />` affichant ΔCA cumulé
- Loading state : spinner + message "simulation en cours (cache miss, ~5s)"

**Données** : `useSimulate()` avec gestion fine du loading.

**Comportement** :
- Au mount : charge le scénario par défaut (SC-L2a) depuis le cache — instantané
- Sur changement de params : nouveau POST /simulate
- Si le hash existe en cache : réponse instantanée
- Sinon : spinner + Mesa tourne côté backend

### 10.6 Multi-rôle

- **Direction réseau** : landing = Page 1 (vue consolidée)
- **Manager magasin** : landing = Page 2 pour son magasin (via paramètre URL ou stocké en local)
- Le `<RoleSwitcher />` permet de basculer librement (utile pour la démo — on veut pouvoir montrer les deux vues)

---

## 11. Phase 1 — scope & non-scope

### 11.1 Non négociable

- [ ] Ingestion Excel → Parquet normalisé avec validation pydantic
- [ ] KPI engine avec les 30 KPIs définis (au moins tous ceux du dashboard)
- [ ] Segmentation K-Means produisant `archetypes.json`
- [ ] Formule H5 implémentée et testée
- [ ] Moteur de règles avec au minimum 5 règles (cf. §7.2)
- [ ] Mesa : ClientAgent + StoreAgent + VisaudioModel + calibration baseline
- [ ] Scénarios SC-BASE **et** SC-L2a (hero) calibrés et joués — minimum absolu pour que le pitch tienne
- [ ] FastAPI avec endpoints GET /kpis, GET /archetypes, GET /diagnostics, POST /simulate
- [ ] Pré-chauffage au démarrage du backend
- [ ] Dashboard React avec Page 1, Page 2, Page 3 fonctionnelles
- [ ] Multi-rôle opérationnel (switch Direction/Manager)
- [ ] Un script CLI `python -m src.cli refresh` qui regénère le Parquet + JSON KPIs + archétypes en un appel

### 11.2 Nice-to-have (peut glisser en Phase 2)

- Page Segments (visualisation des archétypes K-Means)
- 4-5e scénarios Mesa (SC-L2b, SC-L1a, SC-L4a, SC-L5a) — SC-L2a + SC-BASE suffisent au minimum
- Export PDF du diagnostic par magasin
- Comparateur de scénarios côte-à-côte
- Pagination / filtres avancés sur le drill-down
- Toutes les règles de diagnostic au-delà des 5 prioritaires

### 11.3 Explicitement hors-scope Phase 1

- Branchement temps réel sur un SI externe (Phase 2)
- Modèle ML prédictif (Phase 2)
- Authentification / rôles persistés (Phase 2)
- Base de données (Phase 2 : PostgreSQL)
- Multi-tenant (autres clients que Visaudio)
- Édition des règles depuis l'UI

---

## 12. Tests

### 12.1 Stratégie

Coverage cible :
- `src/kpi/` : **≥ 90 %** (business-critical, maths)
- `src/rules/` : **≥ 90 %**
- `src/ingestion/` : **≥ 80 %**
- `src/simulation/` : **≥ 70 %** (Mesa partiellement couvert par le backtest)
- `src/api/` : **≥ 80 %**

### 12.2 Tests prioritaires

- **KPI unitaires** : chaque fonction KPI testée avec un DataFrame de 5-10 lignes forgé à la main, avec au moins un cas nominal + un edge case (DataFrame vide, NaN, un seul magasin).
- **H5 exhaustivement testé** : la formule hero doit être testée avec plusieurs segments et plusieurs magasins pour vérifier le comportement du top-quartile.
- **Pydantic ingestion** : tests de rejet sur les règles métier (gamme sur non-verre, qte=0, etc.).
- **Rules engine** : chaque règle YAML testée avec des entrées qui la déclenchent et qui ne la déclenchent pas.
- **Calibration backtest** : un test de régression qui vérifie que le modèle calibré reste dans les tolérances.
- **API** : test d'intégration FastAPI avec TestClient sur chaque endpoint.

### 12.3 Intégration
Un test end-to-end qui :
1. Part de `data/samples/sample_500.xlsx`
2. Exécute le pipeline complet (ingestion → KPI → diagnostic → 1 scénario Mesa)
3. Vérifie que les outputs JSON ont la structure attendue

---

## 13. Structure de fichiers

```
visaudio/
├── src/
│   ├── __init__.py
│   ├── cli.py                      # entrypoint CLI (refresh pipeline, run backend)
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── schemas.py              # pydantic models
│   │   ├── excel_parser.py
│   │   └── normalization.py        # → Parquet
│   ├── segmentation/
│   │   ├── __init__.py
│   │   ├── features.py             # build client feature vector
│   │   └── kmeans.py               # clustering + labelling
│   ├── kpi/
│   │   ├── __init__.py
│   │   ├── cadrage.py              # C1-C8
│   │   ├── hero.py                 # H1-H10 (inclus H5)
│   │   ├── retention.py            # R1-R5
│   │   ├── benchmark.py            # B1-B4
│   │   ├── conventionnement.py     # D1-D4
│   │   ├── signals.py              # X1-X5
│   │   └── pipeline.py             # orchestrateur qui produit kpis.json
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── engine.py               # lit rules.yaml, évalue, produit findings
│   │   └── rules.yaml              # définitions déclaratives
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── store.py
│   │   ├── model.py                # VisaudioModel(mesa.Model)
│   │   ├── archetypes.py           # chargement K-Means + application agent
│   │   ├── calibration.py          # backtest + tuning
│   │   ├── scenarios.py            # définitions SC-*
│   │   ├── runner.py               # batch runner (N réplications)
│   │   └── metrics.py              # DataCollector
│   └── api/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app
│       ├── endpoints.py            # routes
│       ├── cache.py                # cache Mesa runs
│       └── prewarm.py              # pré-chauffage au démarrage
├── dashboard/
│   └── src/                        # cf. §10.1
├── tests/
│   ├── test_ingestion/
│   ├── test_kpi/
│   │   ├── test_hero.py            # H5 exhaustivement
│   │   └── ...
│   ├── test_rules/
│   ├── test_simulation/
│   ├── test_api/
│   └── test_e2e/
├── data/
│   ├── raw/modele_donnees_optique.xlsx
│   ├── samples/sample_500.xlsx
│   └── processed/
│       ├── sales.parquet
│       ├── kpis.json
│       ├── archetypes.json
│       ├── diagnostics.json
│       ├── rejected_rows.json
│       └── mesa_runs/<hash>.json
└── docs/
    └── specs/
        └── architecture-spec.md    # ce document
```

---

## 14. Annexes

### 14.1 Résumé des décisions (table de référence)

Cf. §2. Relire avant toute décision d'implémentation qui semble contradictoire.

### 14.2 Chiffres cibles pour la démo

| Élément | Valeur | Source |
|---|---|---|
| CA total réseau | ~9.1 M€ | H5 |
| Panier moyen | ~196 € | C4 |
| Clients uniques | ~21 K | C6 |
| **Opportunité upsell annuelle** | **~820 K€** | H5 |
| Opportunité par magasin (worst) | ~142 K€ | H6 |
| ΔCA cumulé 36 mois (SC-L2a) | ~1.2 M€ (CI ±180 K€) | Mesa |

**Tous les chiffres sont illustratifs** — à remplacer par les valeurs réelles après exécution du pipeline.

### 14.3 Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Calibration Mesa ne converge pas | Moyen | Élevé | Plan B D9 : projection qualitative + H5 porte le pitch |
| Pré-chauffage Mesa trop lent au démarrage | Faible | Moyen | Réduire n_replications à 10, ou réduire à 4 scénarios |
| Segmentation K-Means donne des clusters mal interprétables | Moyen | Moyen | Fallback sur segmentation manuelle par règles (âge, panier) |
| Un magasin a trop peu de données pour H6 | Faible | Faible | Seuil minimum de 500 ventes, sinon "données insuffisantes" |
| Le dashboard n'est pas "wow" malgré Mesa | Faible | Élevé | Polish visuel dédié à la page 3 + scénario SC-L2a prêt-à-jouer |

---

**Fin du document.**
