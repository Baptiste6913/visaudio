# Lessons learned

Journal des retours d'expérience, pièges rencontrés, décisions.

## Format

```
## YYYY-MM-DD — Titre court
**Contexte :** ...
**Problème :** ...
**Solution / décision :** ...
**Pour la prochaine fois :** ...
```

## 2026-04-08 — pandas 3.0 défaut datetime64[us] vs [ns]
**Contexte :** Task 3 du plan P1. Test `test_returns_expected_dtypes` échouait sur `date_facture` parce que la spec §4.1 exige `datetime64[ns]` mais pandas 3.0 renvoie `datetime64[us]` par défaut via `pd.to_datetime()`.
**Problème :** `assert df["date_facture"].dtype.name == "datetime64[ns]"` → `'datetime64[us]' == 'datetime64[ns]'` FAIL.
**Solution :** Ajouter `.astype("datetime64[ns]")` explicitement après `pd.to_datetime()` dans `_coerce_dtypes`.
**Pour la prochaine fois :** Sur pandas 3.0, toujours être explicite sur la précision temporelle si on déclare un dtype cible dans une spec. Ne pas faire confiance au défaut. Même règle pour pyarrow qui peut écrire en `[us]` sans qu'on le remarque.

## 2026-04-08 — P1 clos : hero chiffre 81 K€/an (vs pitch target 800 K€)
**Contexte :** Fin du plan P1. Pipeline CLI end-to-end exécutée sur les 79 200 lignes réelles.
**Problème :** Le chiffre hero `opportunite_upsell_annuelle` produit par H5 sur les vraies données vaut **81 K€/an** (~0.9 % du CA total 9.1 M€), soit ~10× moins que la valeur illustrative "800 K€" utilisée dans le brainstorming.
**Analyse :**
- La formule per-cell avec `max(0, gap)` clamping est conservatrice : toute cellule (segment, ville) au-dessus du Q75 de son segment contribue 0.
- La segmentation P1 est `tranche_age` (5 buckets d'âge seulement) — très grossière. P2 remplacera ça par K-Means sur 9 features (age, sexe, conv, panier, freq, gamme, cross-sell, LIBRE, top3). Plus de granularité → plus d'hétérogénéité inter-ville captée → gaps plus grands → chiffre attendu à la hausse.
- 81 K€ reste un chiffre défendable, juste moins spectaculaire.
**Décision :** Accepter le chiffre tel quel pour P1, reporter la re-calibration à P2 quand K-Means donnera des archétypes fins. Ne pas tuner la formule pour "gonfler" le chiffre — ça contredirait la philosophie "défendable devant un comex".
**Pour la prochaine fois :** Quand on écrit un chiffre illustratif dans un brainstorming, le marquer explicitement comme "*à calibrer*" et ne pas en faire une cible de validation. Les chiffres réels doivent émerger des données, pas des pitchs.

## 2026-04-08 — Noms de villes exacts dans la source
**Contexte :** Smoke test d'ingestion sur `sample_500.xlsx` après T3.
**Problème :** Le skill `visaudio-data-model` et les exemples du spec utilisaient `Carentan` et `Cherbourg`. La source Excel réelle contient `Carentan-les-Marais` et `Cherbourg-en-Cotentin`. De plus, le sample initial n'était que les 500 premières lignes → 100 % Avranches (tri par ville).
**Solution :**
1. Régénéré `sample_500.xlsx` en stratifié (83-84 lignes par ville, exactement 500 au total, seed 42).
2. Mis à jour `visaudio-data-model/SKILL.md` avec les 6 noms exacts + volumes par ville.
3. Mis à jour les exemples JSON dans `architecture-spec.md`.
**Distribution réelle des villes (sur 79 200 lignes)** : Cherbourg-en-Cotentin 30 306, Avranches 15 687, Rampan 15 013, Carentan-les-Marais 10 274, Yquelon 7 101, **Coutances 819 (magasin marginal)**.
**Pour la prochaine fois :** Toujours valider les valeurs uniques des colonnes catégorielles critiques sur la source avant de cimenter des noms dans les skills/specs. Un sample stratifié est essentiel pour que les tests E2E soient représentatifs.

## 2026-04-08 — Pydantic model_validator errors ont un loc vide
**Contexte :** Task 3 du plan P1. Extraction de la "reason" d'un rejet de ligne.
**Problème :** Les erreurs provenant d'un `@model_validator(mode="after")` ont `loc=()`. Mon extraction `".".join(str(p) for p in loc)` produisait `""`, et la reason devenait `": Value error, gamme_verre_visaudio must be None..."`.
**Solution :** Helper `_format_validation_error` qui (1) strippe le préfixe `"Value error, "` que pydantic ajoute, (2) renvoie `msg` seul quand `loc` est vide, (3) renvoie `"{field}: {msg}"` sinon.
**Pour la prochaine fois :** Toujours tester le chemin d'erreur pour les `model_validator` (pas juste les contraintes de champ). Le shape d'erreur pydantic est différent.
