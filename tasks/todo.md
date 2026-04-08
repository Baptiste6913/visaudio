# TODO — Visaudio

## En cours

- [x] Initialisation de la structure du projet

## À faire (backlog)

### Ingestion
- [ ] Écrire le parseur Excel principal (`src/ingestion/excel_parser.py`)
- [ ] Définir les schémas pydantic pour chaque feuille
- [ ] Tests d'ingestion sur l'échantillon 500 lignes

### KPI
- [ ] Lister les KPIs prioritaires (spec dans `docs/specs/`)
- [ ] Implémenter le moteur de calcul
- [ ] Tests unitaires KPIs

### Rules / diagnostic
- [ ] Formaliser les règles métier
- [ ] Moteur de règles (déclaratif vs impératif — à décider)

### Simulation
- [ ] POC Mesa : agent magasin + agent client
- [ ] Calibrage sur données réelles

### Dashboard
- [ ] Layout de base (Tailwind + React Router)
- [ ] Premier graphique Recharts branché sur API mock

### API
- [ ] Squelette FastAPI
- [ ] Endpoint `/kpi/{name}`
