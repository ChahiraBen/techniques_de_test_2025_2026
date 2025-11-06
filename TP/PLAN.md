# TODO
# PLAN.md — Plan de tests du composant Triangulator  

## 1️ Objectifs & périmètre

### Objectifs
- Vérifier l’exactitude de l'algorithme de triangulation.  
- Assurer la conformité de l'API exposée (contrat, erreurs, formats).  
- Mesurer la performance (triangulation + sérialisation binaire).  
- Garantir un niveau de qualité (couverture, lint, doc).  

### Périmètre
- Service **Triangulator** uniquement.  
- Tests unitaires (binaire, cœur algo), tests API (Flask), tests d'intégration (Triangulator ↔ PointSetManager mocké), tests de performance séparés.  

---

## 2️ Niveaux de tests

### A. Tests unitaires (comportement)

#### Sérialisation binaire — 'PointSet'

1. **Décoder un PointSet valide**  
   - Pourquoi : vérifier l'interprétation correcte d'un buffer binaire  
   - Comment : buffer de 3 points connus → liste '[(0,0), (1,0), (0,1)]'  
   - Attendu : égalité exacte (tolérance flottants si nécessaire)

2. **Décoder un PointSet tronqué**  
   - Pourquoi : données incomplètes → erreur  
   - Comment : annonce 3 points mais n'en contient que 2  
   - Attendu : exception de type explicite  

3. **Encoder puis décoder un PointSet (round-trip)**  
   - Pourquoi : cohérence encodage/décodage  
   - Comment : encode → decode → comparer  
   - Attendu : égalité  

4. **Points invalides / NaN / Inf**  
   - Pourquoi : robustesse des entrées  
   - Attendu : rejet / exception claire  

5. **Doublons**  
   - Pourquoi : comportement défini si des points sont identiques  
   - Attendu : soit accepté, soit rejet documenté  

---

#### Sérialisation binaire — 'Triangles'

6. **Décoder des Triangles valides**  
   - Pourquoi : lecture correcte de la seconde partie du format  
   - Comment : 4 points + 2 triangles → cohérence des indices  
   - Attendu : indices dans '[0..N-1]', pas d'out-of-range  

7. **Indices triangle hors bornes / négatifs**  
   - Pourquoi : robustesse  
   - Attendu : exception claire  

8. **Round-trip Triangles**  
   - Pourquoi : encode → decode → égalité  

---

#### Algorithme de triangulation

9. **Moins de 3 points**  
   - Attendu : 0 triangle  

10. **Trois points formant un triangle**  
    - Input : '[(0,0),(1,0),(0,1)]'  
    - Attendu : 1 triangle '[(0,1,2)]' (ou équivalent topologique)  

11. **Trois points colinéaires**  
    - Input : '[(0,0),(1,0),(2,0)]'  
    - Attendu : 0 triangle  

12. **Carré de 4 points**  
    - Input : '[(0,0),(1,0),(1,1),(0,1)]'  
    - Attendu : 2 triangles cohérents, pas de recouvrement  

13. **Cas “grille”, “cercle”, “aléatoire”**  
    - Pourquoi : variété de distributions  
    - Attendu : maillage sans intersections ni triangles dégénérés  

14. **Stabilité numérique / tolérance**  
    - Pourquoi : flottants presque colinéaires  
    - Attendu : comportement documenté et testé  

> Optionnel : si je vais faire Delaunay, ajoute des tests de propriété du cercle circonscrit (aucun point à l'intérieur).

---

### B. Tests API (Flask) / intégration légère

1. **Happy path**  
   - POST '/triangulate' avec 'point_set_id'  
   - Mock PointSetManager → renvoie un 'PointSet' binaire (carré)  
   - Attendus : '200 OK', 'Content-Type: application/octet-stream', buffer contenant 2 triangles cohérents  

2. **'point_set_id' introuvable**  
   - Mock PSM → '404 Not Found'  
   - Attendu : '404' côté Triangulator, message d'erreur clair  

3. **Timeout PSM / 5xx PSM**  
   - Attendu : '502/504' (au choix mais documenté), pas de crash  

4. **Entrée invalide**  
   - JSON mal formé / 'Content-Type' incorrect / body vide  
   - Attendu : '400 Bad Request' avec message utile  

5. **Taille d'entrée/sortie**  
   - Attendu : gestion mémoire raisonnable, pas d'explosion de temps ou d'erreur silencieuse  

---

## 3️ Tests de performance (séparés)

> Marqués '@pytest.mark.perf', exclus des tests unitaires.

1. **Triangulation grands ensembles**  
   - Jeux : 10², 10³, 10⁴ points (selon la machine)  
   - Mesure : temps / complexité apparente  
   - Attendu : croissance “raisonnable” (éviter explosion), fixer un budget par palier et l'ajuster  

2. **Encodage/Décodage binaire**  
   - Mesure : temps moyen par taille (point sets variés)  
   - Attendu : coûts linéaires vs nombre de points/triangles  

> Pour la reproductibilité, fixer une 'seed' lors de la génération aléatoire.  

---

## 4️ Couverture & qualité

- **Couverture** : 'coverage' sur modules de logique (hors perf)  
  - **Attendu** : ≥ 90 % sur 'core', 'binary', 'client_psm', 'api'  
- **Lint** : 'ruff check' sans erreur bloquante  
- **Doc** : docstrings → 'pdoc3' génère la documentation HTML  

---

## 5️ Données de test & cas limites

- <3 points, points colinéaires, points doublons  
- Flottants spéciaux (NaN/Inf) → rejet  
- Distributions : grille, cercle, clusters, aléatoire uniforme  
- **Tolérance flottants** : 'math.isclose' / 'pytest.approx'  
- **Endianness** : tests explicites en little-endian  
- **Dégénérescences** : triangles d'aire ≈ 0 → ignorés  

---

## 6️ Critères d'acceptation

- Tous les tests unitaires & API passent (hors '@perf')  
- 'make perf_test' respecte les budgets  
- Couverture ≥ 90 %  
- 'ruff check' OK  
- Documentation générée ('pdoc3')  
- Erreurs documentées (messages et codes HTTP cohérents)  

---

## 7️ Organisation pratique

### Structure des tests
text
tests/
├─ unit/
│  ├─ test_binary.py
│  ├─ test_core.py
│  └─ test_api.py
├─ integration/
│  └─ test_end_to_end.py
└─ performance/
   └─ test_perf.py

### Commandes Make
make test         # pytest -q  
make unit_test    # pytest -q -m 'not perf'  
make perf_test    # pytest -q -m perf  
make coverage     # coverage run -m pytest -q -m 'not perf' && coverage html  
make lint         # ruff check .  
make doc          # pdoc --html triangulator -o docs --force  

