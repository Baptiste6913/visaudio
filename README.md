# Visaudio

Plateforme d'analyse et de simulation pour la filière optique.

## Modules

- **Ingestion** — parseurs Excel vers formats normalisés
- **KPI** — moteur de calcul des indicateurs métier
- **Rules** — moteur de règles / diagnostic
- **Simulation** — agents Mesa pour tests de scénarios
- **Dashboard** — interface React + Tailwind + Recharts

## Démarrage rapide

### Backend Python

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows bash
pip install -r requirements.txt
pytest
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

## Structure

Voir [`CLAUDE.md`](./CLAUDE.md) et [`docs/architecture.md`](./docs/architecture.md).
