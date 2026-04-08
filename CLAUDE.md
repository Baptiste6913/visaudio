# Visaudio Optique Analytics

## WHAT
Outil d'analyse et de simulation multi-agents pour un réseau de 6 magasins
d'optique en Normandie (client Visaudio). Données : ~80K lignes de factures
optique (verres, montures, solaire) de 2023 à 2025.

## WHY
Transformer l'Excel descriptif en outil prédictif/prescriptif :
- KPIs dérivés que le client n'a pas (upsell, LTV, saisonnalité, dépendance conventionnement)
- Simulation multi-agents pour tester des scénarios business (what-if)
- Diagnostic automatique par magasin avec recommandations
- 100% local, zéro API externe (Phase 1)

## Stack
- Backend : Python 3.11+, pandas, Mesa 3 (agent-based modeling), scikit-learn
- Frontend : React + TypeScript + Vite + Tailwind + Recharts + shadcn/ui
- Pas de BDD en phase 1 : JSON/Parquet comme store
- (Futur) FastAPI + PostgreSQL + Claude API

## HOW
- Build backend : `pip install -e .` ou `pip install -r requirements.txt`
- Build frontend : `cd dashboard && npm install && npm run dev`
- Tests : `pytest tests/ -v`
- Lint : `ruff check src/` et `cd dashboard && npm run lint`

## Conventions
- Python : PEP8, type hints obligatoires, docstrings Google style
- React : functional components, hooks, pas de class components
- Nommage fichiers : snake_case Python, kebab-case React
- Commits : conventional commits (feat:, fix:, chore:, docs:, test:)
- Toujours vérifier que les tests passent avant de commit

## Architecture clé
- `src/ingestion/` : lit l'Excel, produit un DataFrame normalisé
- `src/kpi/` : calcule les KPIs dérivés par magasin
- `src/rules/` : moteur de règles heuristique pour le diagnostic
- `src/simulation/` : modèle Mesa avec agents Client et Magasin
- `dashboard/` : React app, consomme les JSON produits par le backend

## Règles critiques
- JAMAIS de données client en clair dans les commits (anonymiser)
- Toujours travailler avec les échantillons dans `data/samples/` pour le dev
- Si un test échoue après un changement, corriger AVANT de continuer
- Documenter toute leçon dans `tasks/lessons.md` après correction
