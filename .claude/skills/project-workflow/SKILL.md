---
name: project-workflow
description: Workflow de développement du projet Visaudio. Déclenche à chaque début de tâche.
---

# Workflow Visaudio

## Cycle de développement

1. **PLANIFIER** : comprendre la tâche, lire la spec si elle existe.
2. **TESTER D'ABORD** : écrire les tests (`pytest`) avant le code.
3. **IMPLÉMENTER** : code minimal qui fait passer les tests.
4. **REVIEWER** : lancer le subagent `code-reviewer`.
5. **COMMIT** : conventional commits (`feat:` / `fix:` / `test:` / `docs:` / `chore:`).
6. **DOCUMENTER** : si erreur corrigée, mettre à jour `tasks/lessons.md`.

## Commandes

- Tests : `pytest tests/ -v --tb=short`
- Lint Python : `ruff check src/`
- Frontend : `cd dashboard && npm run dev`
- Pipeline complet : `python src/main.py --input data/raw/modele_donnees_optique.xlsx`

## Règles critiques

- Toujours travailler avec `data/samples/` pour le dev (**pas** le fichier complet).
- **Jamais** de données client en clair dans les commits.
- Si un test échoue, **corriger AVANT** de passer à la suite.
