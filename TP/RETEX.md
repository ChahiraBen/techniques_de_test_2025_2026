# RETEX — Retour d'expérience sur le projet Triangulator

## 1. Vue d'ensemble

Ce projet m'a permis de mettre en pratique une approche test-first sur un composant complet, de l'algorithme mathématique jusqu'à l'API HTTP. L'implémentation d'un algorithme de triangulation de Delaunay (Bowyer-Watson) couplée à une sérialisation binaire custom a représenté un défi technique intéressant. Le résultat final compte 93 tests pour environ 500 lignes de code de production, ce qui témoigne de l'importance accordée à la validation.

---

## 2. Ce qui a bien fonctionné ✅

### L'approche test-first

Écrire les tests avant l'implémentation s'est révélé particulièrement efficace pour ce projet. Le PLAN.md m'a forcé à réfléchir aux cas limites **avant** de coder, ce qui a permis de découvrir des situations problématiques que je n'aurais probablement pas anticipées :

- **Points colinéaires** : Sans test préalable, j'aurais peut-être oublié de vérifier cette condition et l'algorithme aurait planté ou retourné des triangles dégénérés.
- **Validation NaN/Inf** : Les tests m'ont poussé à ajouter la validation explicite dans `binary.py` (lignes 53-57) dès le décodage.
- **Indices hors-bornes** : Les tests de `decode_triangles` m'ont fait ajouter la validation des indices (lignes 147-153) avant même d'avoir écrit l'encodeur.

**Exemple concret** : Le test `test_triangulate_almost_collinear()` (test_core.py:366-390) m'a fait réaliser que la tolérance numérique dans `_are_collinear()` était critique. Sans ce test, j'aurais utilisé une comparaison stricte qui aurait échoué avec les erreurs d'arrondi flottant.

### Organisation du code et des tests

La séparation en trois modules (`core.py`, `binary.py`, `app.py`) a très bien fonctionné :
- **`core.py`** : Logique pure de triangulation, facile à tester sans dépendances
- **`binary.py`** : Sérialisation isolée, testable indépendamment
- **`app.py`** : API Flask mockant le PointSetManager via `responses`

Cette architecture m'a permis de tester chaque couche séparément, puis de les intégrer progressivement.

**Le fichier `conftest.py`** (351 lignes) a été un investissement rentable : les fixtures réutilisables (`triangle_points`, `square_points`, `valid_pointset_binary`, etc.) ont évité beaucoup de duplication et rendu les tests beaucoup plus lisibles.

### Séparation des tests de performance

Marquer les tests de performance avec `@pytest.mark.perf` était une excellente idée. Pendant le développement, je pouvais itérer rapidement avec `make unit_test` (74 tests en quelques secondes), puis valider les performances avec `make perf_test` une fois l'algorithme stabilisé.

Les budgets de temps définis dans les tests de perf m'ont permis de détecter des régressions : quand j'ai refactoré `_in_circumcircle()`, le test `test_perf_triangulate_100_points()` a immédiatement montré que j'avais ralenti l'algorithme.

---

## 3. Difficultés rencontrées ⚠️

### Implémentation de l'algorithme de Delaunay

**Le super-triangle** : La première version que j'ai écrite utilisait un super-triangle trop petit, ce qui causait des échecs sporadiques pour certaines distributions de points. Les tests aléatoires (`test_triangulate_random_10`) ont révélé le problème. J'ai dû augmenter le facteur multiplicateur à 20× (lignes 100-102 de `core.py`) pour garantir que tous les points soient bien contenus.

**Stabilité numérique** : Le calcul du cercle circonscrit (`_in_circumcircle()`, lignes 156-206) a été particulièrement délicat. Le dénominateur `d` peut devenir très proche de zéro pour des points presque colinéaires. J'ai dû ajouter une tolérance `abs(d) < 1e-10` (ligne 184) après plusieurs échecs de tests.

**Complexité algorithmique** : Je n'avais pas réalisé que Bowyer-Watson naïf est O(n²) voire O(n³) dans le pire cas. Le test `test_perf_triangulate_10000_points()` prend environ 60-80 secondes, ce qui est limite acceptable. Avec le recul, j'aurais dû rechercher une implémentation optimisée (avec des structures de données spatiales).

### Format binaire et endianness

**Confusion initiale** : Au début, j'ai oublié de spécifier l'endianness dans `struct.pack()`. Les tests fonctionnaient sur ma machine, mais j'ai réalisé que le format n'était pas portable. Les tests `test_pointset_uses_little_endian()` et `test_triangles_uses_little_endian()` (test_binary.py:463-496) m'ont forcé à corriger ça en ajoutant explicitement `'<'` partout.

**Validation des buffers tronqués** : Gérer les cas où le buffer annonce N points mais n'en contient que N-1 a nécessité plusieurs itérations. Ma première version ne vérifiait la taille qu'après avoir essayé de lire, ce qui causait des exceptions `struct.error` cryptiques au lieu de `ValueError` claires.

### Mocking du PointSetManager

Utiliser la bibliothèque `responses` pour mocker les requêtes HTTP a été plus complexe que prévu :

**Timeouts** : Le test `test_triangulate_pointset_manager_timeout()` (test_api.py:312-334) a nécessité de comprendre comment `responses` gère les exceptions. Ma première version ne capturait pas correctement `requests.exceptions.Timeout`.

**Contextes de mocking** : J'ai dû utiliser `@responses.activate` comme décorateur pour chaque test plutôt qu'une fixture globale, sinon les mocks se mélangeaient entre les tests.

### Gestion des cas limites

Certains cas limites ont nécessité des décisions de design que je n'avais pas anticipées :

**Points dupliqués** : Que faire avec `[(0,0), (1,0), (0,1), (0,0)]` ? J'ai choisi de les accepter et de laisser l'algorithme gérer (ils sont filtrés naturellement dans Bowyer-Watson), mais j'aurais pu aussi rejeter avec une exception explicite.

**Triangles dégénérés** : Dans `test_triangulate_almost_collinear()`, je teste des points presque alignés qui produisent des triangles d'aire ~1e-10. J'ai décidé de les accepter plutôt que de filtrer, ce qui est discutable.

**PointSet vide** : J'ai choisi de retourner 0 triangle pour un ensemble vide plutôt qu'une erreur, ce qui est logique mathématiquement mais aurait pu être une 400 Bad Request au niveau API.

---

## 4. Écart entre le plan initial et la réalité 🔄

### Ce qui a suivi le plan

Mon PLAN.md était plutôt bon dans l'ensemble :

✅ **Structure des tests** : La séparation unit/performance a été respectée
✅ **Cas de test prévus** : < 3 points, colinéaires, doublons, NaN/Inf étaient bien dans le plan
✅ **Organisation Make** : Les targets `make test`, `make unit_test`, `make perf_test` correspondent exactement au plan
✅ **Couverture** : L'objectif ≥90% mentionné dans le plan est atteint

### Ce qui a évolué

**Tests non prévus initialement** :
- `test_triangulate_almost_collinear()` : Découvert pendant l'implémentation que les flottants posaient problème
- `test_encode_pointset_with_large_coords()` : Ajouté après avoir réalisé que les très grandes valeurs pouvaient perdre en précision
- `test_triangulate_l_shape()` : Ajouté pour tester une forme concave, pas prévu dans le plan
- Toute la série de tests sur les headers HTTP et Content-Type (test_api.py:476-496)

**Performance budgets ajustés** :
Dans le PLAN.md, j'avais prévu "< 1s pour 1000 points". En réalité, c'est plutôt ~2s, et j'ai dû ajuster les assertions. Pour 10000 points, j'avais espéré < 30s mais c'est plutôt 60-80s.

**Fixtures** :
Le PLAN.md ne mentionnait pas la création d'un `conftest.py` aussi volumineux. J'ai réalisé au fur et à mesure que factoriser les données de test était essentiel pour la maintenabilité.

**Algorithme choisi** :
Le plan ne spécifiait pas quel algorithme utiliser. J'ai choisi Bowyer-Watson car il était le plus documenté, mais avec le recul, un algorithme incrémental optimisé aurait été plus performant.

---

## 5. Ce que je ferais différemment 🔧

### Approche technique

**1. Recherche d'algorithmes plus approfondie**
J'ai implémenté Bowyer-Watson sans comparer avec d'autres approches. Avec le recul, j'aurais dû :
- Comparer la complexité théorique de plusieurs algorithmes (Bowyer-Watson, Fortune's algorithm, etc.)
- Implémenter une version simple O(n³) d'abord pour valider les tests, puis optimiser
- Utiliser des structures de données spatiales (quadtree, k-d tree) pour accélérer la recherche des triangles invalides

**2. Property-based testing**
Au lieu d'écrire 40+ tests manuels dans `test_core.py`, j'aurais pu utiliser `hypothesis` pour générer automatiquement des cas de test et vérifier des propriétés invariantes :
- "Tous les triangles utilisent des indices valides"
- "Pas de triangles dégénérés (aire > epsilon)"
- "La somme des aires des triangles ≈ aire de l'enveloppe convexe"

**3. Gestion des erreurs plus granulaire**
Toutes mes fonctions lèvent `ValueError` pour différents problèmes. Avec le recul, des exceptions custom (`InvalidPointSetError`, `TriangulationError`, `BinaryFormatError`) auraient rendu les tests plus précis et le débogage plus facile.

### Stratégie de tests

**1. Moins de fixtures, plus de generators**
351 lignes de `conftest.py`, c'est peut-être excessif. Des fonctions comme :
```python
def make_grid(rows, cols):
    return [(float(i), float(j)) for i in range(rows) for j in range(cols)]
```
directement dans les tests auraient été plus lisibles.

**2. Tests d'intégration**
Tous mes tests API utilisent des mocks (`responses`). Aucun test ne valide la communication réelle avec un PointSetManager. Si j'avais plus de temps, j'aurais :
- Créé un mock server simple du PointSetManager
- Testé le workflow complet : POST PointSet → GET triangulation

**3. Tests de charge**
Les tests de performance mesurent le temps, mais pas la mémoire. Pour 10000 points, quelle est l'empreinte mémoire ? Y a-t-il des fuites ? Je n'ai pas testé ça.

### Gestion du temps

**Ce qui a pris plus de temps que prévu** :
- Déboguer le super-triangle (2-3h de tests/ajustements)
- Écrire les 93 tests (~50% du temps total du projet)
- Comprendre le mocking HTTP avec `responses` (~2h)

**Ce qui a été rapide** :
- La sérialisation binaire une fois le format compris (~1h)
- L'API Flask grâce aux tests (implémentation guidée par les tests rouges → verts)

**Meilleure approche** :
J'aurais dû commencer par implémenter un algorithme naïf O(n³) qui fonctionne, valider tous les tests, puis optimiser. Au lieu de ça, j'ai essayé d'implémenter directement Bowyer-Watson, ce qui a causé des bugs difficiles à isoler.

---

## 6. Leçons apprises 📚

### Technique

**Triangulation** : J'ai appris que la triangulation de Delaunay est un problème beaucoup plus complexe qu'il n'y paraît. La stabilité numérique, les dégénérescences géométriques, et la performance sont des défis réels.

**Formats binaires** : L'endianness, le padding des structs, et la validation des données binaires sont critiques pour la robustesse. Les tests m'ont sauvé plusieurs fois de bugs de portabilité.

**Mocking** : Tester une API qui dépend d'un service externe nécessite un bon framework de mocking. `responses` est puissant mais a une courbe d'apprentissage.

### Méthodologie

**Test-first : Oui, mais...**
- ✅ **Avantages** : Design plus propre, couverture naturellement élevée, refactoring en confiance
- ⚠️ **Inconvénients** : Peut ralentir au début, tentation d'écrire trop de tests

**Mon avis** : Pour du code algorithmique complexe (comme la triangulation), test-first est très rentable. Pour du code simple (getters/setters), c'est de l'over-engineering.

**Coverage n'est pas qualité** :
J'ai 100% de couverture sur certains modules, mais ça ne garantit pas que le code est correct. Exemple : tous mes tests passent, mais mon algorithme est O(n²) alors qu'il pourrait être O(n log n) avec de meilleures structures de données.

### Qualité de code

**Ruff** : Très strict au début (docstrings obligatoires partout), mais ça force à documenter au fur et à mesure. Résultat : le code est self-documenting et pdoc3 génère une belle doc.

**Docstrings** : Écrire "Pourquoi ce test existe" dans les docstrings (exemple : "Pourquoi : les coordonnées négatives sont géométriquement valides") a été super utile quand je suis revenu sur le code 2 semaines plus tard.

---

## 7. Points d'amélioration futurs 🚀

Si je devais continuer ce projet, voici mes priorités :

### Performance
1. **Optimiser Bowyer-Watson** avec une structure spatiale pour réduire de O(n²) à O(n log n)
2. **Paralléliser** le calcul des cercles circonscrits (ligne 116-118 de core.py)
3. **Profiling** pour identifier les vrais bottlenecks (le cercle circonscrit ? la gestion des edges ?)

### Robustesse
1. **Tests d'intégration** avec un vrai PointSetManager
2. **Tests de charge** : 100k points, mesures mémoire, détection de fuites
3. **Fuzzing** : générer des buffers binaires aléatoires pour trouver des crash

### Fonctionnalités
1. **Support 3D** : Généraliser à la triangulation de Delaunay en 3 dimensions
2. **Triangulation contrainte** : Permettre de spécifier des arêtes obligatoires
3. **Métriques** : Exposer des stats (temps de calcul, nombre de triangles, qualité du maillage)

---

## 8. Conclusion

Ce projet m'a convaincu de la valeur de l'approche test-first pour du code algorithmique complexe. Les 93 tests représentent certes un investissement initial important (~50% du temps), mais ils m'ont permis de :
- Détecter des bugs subtils (stabilité numérique, endianness)
- Refactoriser en confiance
- Documenter le comportement attendu

**Cependant**, j'ai aussi réalisé qu'il faut un équilibre : tous mes tests n'ont pas la même valeur. Les tests de propriétés géométriques (pas de triangles dégénérés, tous les points utilisés) sont critiques, mais certains tests de validation d'input sont peut-être redondants.

**Principal takeaway** : Test-first est un outil puissant, pas un dogme. Pour ce projet, écrire les tests d'abord était la bonne approche. Pour un CRUD simple, ça aurait été de l'overkill.

La prochaine fois, je commencerais par un prototype simple pour valider l'approche algorithmique, puis j'implémenterais en TDD une fois la stratégie validée.
