# CLAUDE.md

Ce fichier fournit le contexte au modèle Claude Code lorsqu'il travaille sur ce dépôt.

## Projet : Visaudio

Plateforme d'analyse et de simulation pour la filière optique (audition / vision).
L'objectif est d'ingérer des données Excel brutes, de calculer des KPIs métier,
d'appliquer des règles de diagnostic, et de simuler des scénarios via des agents.

## Stack

- **Backend / data** : Python 3.11+, pandas, openpyxl, pydantic, Mesa (simulation multi-agents)
- **Tests** : pytest
- **API (futur)** : FastAPI
- **Dashboard** : React + TypeScript + Tailwind + Recharts

## Arborescence

- `data/raw/` : fichiers Excel sources (ne pas modifier à la main)
- `data/processed/` : données nettoyées (JSON/Parquet)
- `data/samples/` : échantillons pour tests rapides
- `src/ingestion/` : parseurs Excel
- `src/kpi/` : moteur de KPIs
- `src/rules/` : moteur de règles / diagnostic
- `src/simulation/` : agents Mesa
- `src/api/` : endpoints FastAPI (à venir)
- `dashboard/` : front React
- `tests/` : suite pytest (miroir de `src/`)
- `docs/` : specs et architecture
- `tasks/todo.md` : backlog actif
- `tasks/lessons.md` : retours d'expérience

## Conventions

- Toute nouvelle feature commence par une spec dans `docs/specs/`
- TDD : écrire le test avant l'implémentation
- Ne jamais committer de données sensibles patients dans `data/raw/`
- Les échantillons de `data/samples/` sont anonymisés

## Commandes utiles

```bash
# Tests
pytest tests/ -v

# Dashboard
cd dashboard && npm run dev
```
