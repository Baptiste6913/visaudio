---
name: mesa-simulation
description: Guide pour le modèle de simulation multi-agents Mesa. Déclenche quand on travaille sur src/simulation/.
---

# Simulation Multi-Agents Mesa — Visaudio

## Framework

- **Mesa 3.2+** (`pip install "mesa[rec]"`)
- Docs : https://mesa.readthedocs.io/stable/
- Exemples de référence : **Hotelling's Law**, **El Farol**

## Architecture agents

- **ClientAgent** : archétype client avec comportements d'achat
- **StoreAgent** : magasin avec mix produit et politique prix
- **Environnement** : saisonnalité, conventionnements, tendances

## Calibration

- Les comportements agents **DOIVENT** être calibrés sur les données réelles.
- Utiliser **K-Means** pour créer **6-10 archétypes clients**.
- Features de clustering : `age`, `panier`, `gamme préférée`, `fréquence`, `conventionnement`.
- Probabilités d'achat = fréquences historiques observées par cluster.

## Scénarios

- Chaque scénario modifie **un** paramètre du modèle (prix, gamme, effort).
- Toujours comparer avec un **run baseline** (sans modification).
- Lancer **10+ runs** par scénario pour avoir des intervalles de confiance.
- **1 step = 1 mois**, horizon standard = **36 mois**.
