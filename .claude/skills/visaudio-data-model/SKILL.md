---
name: visaudio-data-model
description: Référence du modèle de données optique Visaudio. Déclenche quand on travaille sur l'ingestion, les KPIs, ou la simulation.
---

# Modèle de données Visaudio Optique

## Colonnes du fichier source (19 colonnes)

- **Ville** : `str` — 6 valeurs exactes : `Avranches`, `Carentan-les-Marais`, `Cherbourg-en-Cotentin`, `Coutances`, `Rampan`, `Yquelon`. Attention : les noms complets (`-les-Marais`, `-en-Cotentin`) doivent être utilisés partout, pas les formes abrégées. Volumes (source complète) : Cherbourg-en-Cotentin 30 306, Avranches 15 687, Rampan 15 013, Carentan-les-Marais 10 274, Yquelon 7 101, **Coutances 819 (très petit — tolérances statistiques relâchées)**.
- **Implantation** : `str` — type de lieu (CENTRE-VILLE, PERIPHERIE, ZONE COMMERCIALE)
- **Secteur économique** : `str` — (Tertiaire, etc.)
- **datefacture** : `datetime` — date de la facture (2023-01 à 2025-12)
- **id Facture rang** : `str` — identifiant facture (format `"XXXXXXXX|N"`)
- **Rang paire** : `int` — rang de la paire dans la facture
- **Famille Article** : `str` — `OPT_VERRE`, `OPT_MONTURE`, `OPT_SOLAIRE`
- **Catégorie géométrie verre** : `str` — `UNIFOCAL`, `MULTIFOCAL`, `null`
- **Gamme verre fournisseur** : `str` — gamme chez le fournisseur
- **Gamme verre Visaudio** : `str` — `ESSENTIEL`, `CONFORT`, `PREMIUM`, `PRESTIGE`, `null`
- **nommarque** : `str` — marque (ESS, HOY, Les Bien Vues, etc.)
- **libelle produit** : `str` — désignation article
- **Qte article** : `int` — quantité
- **CA HT article** : `float` — chiffre d'affaires HT
- **id Client** : `int` — identifiant client unique
- **Conventionnement** : `str` — `LIBRE`, `CSS`, `SANTECLAIR`, `KALIXIA`, `ITELIS`, etc.
- **datenaissance client** : `datetime` — date de naissance
- **Sexe** : `str` — `Femme`, `Homme`
- **Nouveau client / Renouvellement** : `str` — `Nouveau client`, `Renouvellement`, `null`

## Métriques clés du réseau

- **79 200 lignes**, **~21 000 clients uniques**
- **CA total réseau** : ~9 M€ (2023-2025)
- **Panier moyen** : 196 € à 240 € selon magasin
- **Mix CA** : verres 78 %, montures 20 %, solaire 2 %

## Règles métier

- La **gamme Visaudio** ne s'applique qu'aux **verres** (pas montures/solaire).
- Un `id Facture rang` peut contenir plusieurs lignes (verre + monture).
- Le **Rang paire** identifie la paire de lunettes dans la facture.
- **Conventionnement** = réseau de soins du client (impact sur les prix).
