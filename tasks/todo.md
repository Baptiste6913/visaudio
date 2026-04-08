# TODO — Visaudio

## En cours

- [x] Initialisation de la structure du projet
- [x] **P1 — Ingestion + KPI engine** (2026-04-08) — 15 commits, 68 tests green, CLI end-to-end validée sur 79 200 lignes réelles. Hero chiffre : 81 K€/an (à re-calibrer en P2 avec K-Means).
- [ ] **P2 — Segmentation K-Means + Rules engine / diagnostics** (next)

## À faire (backlog)

### P2 — Segmentation + Rules
- [ ] Feature vector par client (`src/segmentation/features.py`)
- [ ] K-Means clustering (6-10 archétypes) + labelling
- [ ] Export `archetypes.json`
- [ ] Ré-intégrer la segmentation K-Means dans H5 (remplacer `tranche_age`)
- [ ] Rules engine déclaratif (`src/rules/engine.py` + `rules.yaml`)
- [ ] Export `diagnostics.json` (findings par magasin)

### P3 — Simulation Mesa
- [ ] ClientAgent + StoreAgent + VisaudioModel
- [ ] Calibration baseline sur 2023-2024, backtest 2025
- [ ] Au minimum scénarios SC-BASE + SC-L2a (hero)
- [ ] 4 scénarios supplémentaires si le budget le permet (SC-L2b, SC-L1a, SC-L4a, SC-L5a)

### P4 — Backend FastAPI
- [ ] Endpoints `/health`, `/kpis`, `/archetypes`, `/diagnostics`, `/scenarios`, `/simulate`
- [ ] Cache Mesa runs par hash de params
- [ ] Pré-chauffage des scénarios démo au démarrage

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
