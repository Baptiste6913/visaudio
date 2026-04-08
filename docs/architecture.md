# Architecture — Visaudio

## Vue d'ensemble

```
Excel brut  ──►  Ingestion  ──►  Données normalisées  ──►  KPI  ──►  Dashboard
                                         │
                                         ├──►  Rules / diagnostic
                                         │
                                         └──►  Simulation (Mesa)
```

## Couches

### 1. Ingestion (`src/ingestion/`)
Lit les fichiers Excel de `data/raw/`, valide via pydantic, et produit des
DataFrames / Parquet normalisés dans `data/processed/`.

### 2. KPI (`src/kpi/`)
Consomme les données normalisées et calcule les indicateurs métier.
Chaque KPI est une fonction pure testable.

### 3. Rules (`src/rules/`)
Moteur de règles de diagnostic. Prend en entrée un état (dict / DataFrame)
et retourne une liste de findings (alerte, recommandation).

### 4. Simulation (`src/simulation/`)
Agents Mesa pour simuler des scénarios (capacité, file d'attente, etc.).

### 5. API (`src/api/`)
FastAPI. Expose KPI, résultats de règles et simulations au dashboard.

### 6. Dashboard (`dashboard/`)
React + TS + Tailwind + Recharts. Consomme l'API.

## Décisions (ADR légers)

À documenter au fil de l'eau dans `docs/specs/`.
