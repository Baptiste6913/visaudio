# TODO — Visaudio

## En cours

- [x] Initialisation de la structure du projet
- [x] **P1 — Ingestion + KPI engine** (2026-04-08) — 15 commits, 68 tests green, CLI end-to-end validée sur 79 200 lignes réelles. Hero chiffre : 81 K€/an (à re-calibrer en P2 avec K-Means).
- [x] **P2 — Segmentation K-Means + Rules engine / diagnostics** (2026-04-08) — 13 commits, 111 tests green, CLI `refresh` umbrella (ingest → segment → kpi → diagnose) validée E2E sur `sample_500.xlsx`. Hero chiffre re-calibré sur 79K : **123 773 €/an** (+52 % vs P1). Voir `lessons.md` pour les 3 findings (sample-size, silhouette OOM, axes de labelling).
- [x] **P3 — Simulation Mesa** (2026-04-09) — 11 commits, 158 tests green. ClientAgent + StoreAgent + VisaudioModel + 6 scénarios + batch runner + calibration + CLI `simulate`. E2E validé sur `sample_500.xlsx`.
- [x] **P4 — Backend FastAPI** (2026-04-09) — 8 commits, 193 tests green. 6 endpoints (health, kpis, archetypes, diagnostics, scenarios, simulate), cache SHA-256, pré-chauffage 6 scénarios, CLI `serve`. E2E validé.

## À faire (backlog)

### P2 — Segmentation + Rules (DONE)
- [x] Feature vector par client (`src/segmentation/features.py`)
- [x] K-Means clustering (6-10 archétypes) + labelling
- [x] Export `archetypes.json`
- [x] Ré-intégrer la segmentation K-Means dans H5 (remplacer `tranche_age`)
- [x] Rules engine déclaratif (`src/rules/engine.py` + `rules.yaml`)
- [x] Export `diagnostics.json` (findings par magasin)

### P3 — Simulation Mesa (DONE)
- [x] ClientAgent + StoreAgent + VisaudioModel
- [x] Archetype loader + seasonality extraction
- [x] 6 scénarios (SC-BASE, SC-L2a, SC-L2b, SC-L1a, SC-L4a, SC-L5a)
- [x] Batch runner avec CI 95% (N réplications Monte Carlo)
- [x] Calibration + backtest utilities
- [x] CLI `simulate` subcommand
- [x] E2E test sur sample_500.xlsx

### P4 — Backend FastAPI (DONE)
- [x] Pydantic schemas (SimulateRequest/Response, Trajectory, ScenarioInfo)
- [x] Cache SHA-256 disk (`data/processed/mesa_runs/<hash>.json`)
- [x] FastAPI app + CORS + lifespan
- [x] GET endpoints: `/health`, `/kpis`, `/archetypes`, `/diagnostics`, `/scenarios`
- [x] POST `/simulate` — cache-first, baseline comparison, ΔCA
- [x] Pré-chauffage 6 scénarios au démarrage
- [x] CLI `serve` subcommand (uvicorn)
- [x] E2E test sur sample_500.xlsx

### P5 — Dashboard React
- [ ] Setup Vite + TS + Tailwind + Recharts + shadcn
- [ ] Client `utils/api.ts` unifié
- [ ] Page 1 — Landing Direction (hero card, KPI row, charts par magasin/segment)
- [ ] Page 2 — Drill-down magasin (KPIs + diagnostic auto + waterfall + tabs)
- [ ] Page 3 — Simulation Mesa (sliders, twin-curve plot, result box)
- [ ] Multi-rôle (Direction / Manager) avec RoleSwitcher

## Lessons à résoudre (deferred dans tasks/lessons.md)

- [ ] `ca_par_mois` : passer à `resample("MS")` pour expliciter les mois à zéro (impact dashboard timeseries)
- [ ] `24 * 30` days → `pd.DateOffset(months=24)` pour exactitude (impact mineur)
- [ ] `index_saisonnalite_par_magasin` : supprimer la copie inutile du df
- [ ] Type hints sur les helpers privés `_build_*` dans `pipeline.py`
- [ ] `test_cohort_retention_curve_is_dict` : renforcer les assertions (vérifier la valeur M+12 pour cohort 2024-02)
