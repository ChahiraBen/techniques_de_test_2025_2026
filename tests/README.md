# Tests du composant Triangulator

Structure complète des tests générée selon PLAN.md et SUJET.md.

## Statistiques

- **93 tests au total**
- **74 tests unitaires** (binary, core, API)
- **20 tests de performance** (marqués `@pytest.mark.perf`)

##  Structure

```
tests/
├── conftest.py                  # Fixtures partagées (points, binaires, mocks)
├── unit/
│   ├── test_binary.py          # 33 tests : sérialisation PointSet/Triangles
│   ├── test_core.py            # 23 tests : algorithme de triangulation
│   └── test_api.py             # 18 tests : API Flask + intégration PSM
└── performance/
    └── test_perf.py            # 20 tests : performance triangulation/binaire
```

##  Exécution des tests

### Tests unitaires uniquement (recommandé pour le développement)
```bash
make unit_test
# ou
pytest -m "not perf"
```

### Tests de performance uniquement
```bash
make perf_test
# ou
pytest -m perf
```

### Tous les tests
```bash
make test
# ou
pytest
```

### Couverture de code
```bash
make coverage
# Génère htmlcov/index.html
```

##  Détail des tests

### test_binary.py (33 tests)
Couvre la sérialisation/désérialisation binaire selon les formats du SUJET.md :

**PointSet** :
- Décodage valide, tronqué, malformé
- Gestion NaN/Inf, doublons, coordonnées négatives/larges
- Encodage et round-trips
- Vérification little-endian explicite

**Triangles** :
- Décodage valide avec validation des indices
- Gestion des indices hors-bornes, négatifs
- Encodage et round-trips
- Cas limites (0 triangle, 1 triangle)

### test_core.py (23 tests)
Couvre l'algorithme de triangulation :

**Cas limites** :
- 0, 1, 2 points → 0 triangle
- 3 points colinéaires → 0 triangle
- 3 points formant triangle → 1 triangle

**Géométries** :
- Carré (4 points) → 2 triangles
- Pentagone → 3 triangles
- Grille 3x3, cercle, points aléatoires

**Validation** :
- Aucun triangle dégénéré (aire ≈ 0)
- Indices valides [0, N-1]
- Tous les points utilisés
- Somme des aires = aire totale

**Robustesse** :
- Points presque colinéaires
- Très petites/grandes coordonnées
- Doublons, lignes verticales/horizontales

### test_api.py (18 tests)
Couvre l'API Flask selon triangulator.yml :

**Happy path** :
- 200 OK avec carré, triangle, PointSet vide
- Content-Type: application/octet-stream

**Erreurs client (400)** :
- UUID invalide, vide, avec caractères spéciaux

**Erreurs PSM (404, 503)** :
- PointSet introuvable → 404
- PSM indisponible → 503
- Timeout réseau → 503/504
- Erreur de connexion → 503

**Erreurs internes (500)** :
- Buffer binaire malformé
- NaN/Inf dans les données
- Échec de l'algorithme (mocké)

**Autres** :
- Méthode HTTP incorrecte → 405
- Grandes données (100 points)
- Points colinéaires, doublons

### test_perf.py (20 tests)
Mesure les performances :

**Triangulation** :
- 10, 100, 1000, 10000 points
- Croissance de la complexité (ratio)
- Grille vs aléatoire vs cercle

**Encodage/Décodage** :
- 100, 1000 points
- Vérification complexité O(n)
- Round-trips

**Bout en bout** :
- Triangulation + encodage (100, 500 points)

**Reproductibilité** :
- Mesures stables sur 5 exécutions

## Critères de réussite

Tous les tests sont conçus pour **échouer** initialement car le code de production n'existe pas encore. C'est normal et attendu dans une approche TDD.

Une fois l'implémentation terminée :
-  `make unit_test` doit passer (tous les tests unitaires)
-  `make perf_test` doit respecter les budgets de temps
-  `make coverage` doit afficher ≥ 90% de couverture
-  `make lint` doit passer sans erreur

## Configuration

- **pytest.ini** : configure les markers (`perf`, `slow`) et options
- **Makefile** : commandes standardisées selon SUJET.md
- **conftest.py** : fixtures réutilisables (évite duplication)

## Dépendances de test

Définies dans `dev_requirements.txt` :
- pytest
- coverage
- responses (mock HTTP)
- ruff
- pdoc3

##  Points clés

1. **Format binaire** : little-endian (`'<'` en struct), validé explicitement
2. **Tolérance flottants** : `pytest.approx` avec `abs=1e-6` ou `rel=1e-5`
3. **Mocking HTTP** : `responses` pour mocker PointSetManager
4. **Séparation perf** : `@pytest.mark.perf` permet exclusion
5. **Reproductibilité** : seeds fixées pour les données aléatoires
6. **Docstrings** : chaque test explique POURQUOI il existe

##  Références

- SUJET.md : spécifications complètes du projet
- PLAN.md : plan de tests détaillé
- triangulator.yml : API du Triangulator
- point_set_manager.yml : API du PointSetManager
