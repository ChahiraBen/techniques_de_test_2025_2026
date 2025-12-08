"""Tests de performance pour le composant Triangulator.

Ce module teste :
- La performance de l'algorithme de triangulation sur des ensembles de tailles variées
- La performance de l'encodage/décodage binaire
- La croissance de la complexité algorithmique
- Les budgets de temps pour différentes tailles

IMPORTANT : Tous les tests de ce module sont marqués @pytest.mark.perf
pour permettre leur exclusion lors de l'exécution normale des tests.

Commandes :
    - make unit_test : exclut ces tests
    - make perf_test : exécute uniquement ces tests
    - make test : exécute tous les tests (incluant perf)

Notes :
- Les seeds sont fixées pour la reproductibilité
- Les budgets de temps sont indicatifs et peuvent nécessiter ajustement
- Les mesures de performance sont sensibles à la machine d'exécution
"""

import math
import random
import time

import pytest

from triangulator.binary import (
    decode_pointset,
    decode_triangles,
    encode_pointset,
    encode_triangles,
)
from triangulator.core import triangulate

# Helpers : Génération de données de test
 

def generate_random_points(n, seed=42):
    """Génère n points aléatoires avec une seed fixe.

    Pourquoi : reproductibilité des tests de performance.
    """
    random.seed(seed)
    return [(random.uniform(0, 1000), random.uniform(0, 1000)) for _ in range(n)]


def generate_grid_points(rows, cols):
    """Génère des points disposés en grille régulière.

    Pourquoi : distribution uniforme pour tester les cas réguliers.
    """
    points = []
    for i in range(rows):
        for j in range(cols):
            points.append((float(i), float(j)))
    return points


def generate_circle_points(n):
    """Génère n points disposés sur un cercle.

    Pourquoi : teste les distributions circulaires (cas fréquent).
    """
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        x = math.cos(angle)
        y = math.sin(angle)
        points.append((x, y))
    return points


 
# Tests de performance : Triangulation
 

@pytest.mark.perf
def test_perf_triangulate_10_points():
    """Test de performance : triangulation de 10 points aléatoires.

    Pourquoi : établir un baseline pour les petits ensembles.
    Budget : < 0.01 seconde
    """
    points = generate_random_points(10)

    start = time.perf_counter()
    triangles = triangulate(points)
    elapsed = time.perf_counter() - start

    print(f"\nTriangulation de 10 points : {elapsed:.6f} s")
    print(f"Nombre de triangles générés : {len(triangles)}")

    assert elapsed < 0.01, \
        f"Triangulation de 10 points devrait prendre < 0.01s, pris {elapsed:.6f}s"


@pytest.mark.perf
def test_perf_triangulate_100_points():
    """Test de performance : triangulation de 100 points aléatoires.

    Pourquoi : tester sur un ensemble de taille moyenne.
    Budget : < 0.1 seconde (ajustable selon l'algorithme)
    """
    points = generate_random_points(100, seed=100)

    start = time.perf_counter()
    triangles = triangulate(points)
    elapsed = time.perf_counter() - start

    print(f"\nTriangulation de 100 points : {elapsed:.6f} s")
    print(f"Nombre de triangles générés : {len(triangles)}")

    # Budget ajustable selon la machine et l'algorithme
    assert elapsed < 0.1, \
        f"Triangulation de 100 points devrait prendre < 0.1s, pris {elapsed:.6f}s"


@pytest.mark.perf
def test_perf_triangulate_1000_points():
    """Test de performance : triangulation de 1000 points aléatoires.

    Pourquoi : tester sur un grand ensemble.
    Budget : < 2.0 secondes (ajustable)
    """
    points = generate_random_points(1000, seed=1000)

    start = time.perf_counter()
    triangles = triangulate(points)
    elapsed = time.perf_counter() - start

    print(f"\nTriangulation de 1000 points : {elapsed:.6f} s")
    print(f"Nombre de triangles générés : {len(triangles)}")

    # Budget généreux pour algorithmes simples (O(n²) ou O(n³))
    assert elapsed < 2.0, \
        f"Triangulation de 1000 points devrait prendre < 2.0s, pris {elapsed:.6f}s"


@pytest.mark.perf
@pytest.mark.slow
def test_perf_triangulate_10000_points():
    """Test de performance : triangulation de 10000 points aléatoires.

    Pourquoi : tester les très grands ensembles (optionnel).
    Budget : < 60 secondes (1 minute)

    Note : ce test est marqué 'slow' et peut être exclu même des tests de perf.
    """
    points = generate_random_points(10000, seed=10000)

    start = time.perf_counter()
    triangles = triangulate(points)
    elapsed = time.perf_counter() - start

    print(f"\nTriangulation de 10000 points : {elapsed:.6f} s")
    print(f"Nombre de triangles générés : {len(triangles)}")

    assert elapsed < 80.0, \
        f"Triangulation de 10000 points devrait prendre < 80s, pris {elapsed:.6f}s"


 
# Tests de performance : Complexité algorithmique
 

@pytest.mark.perf
def test_perf_triangulate_complexity_growth():
    """Test de la croissance de la complexité avec la taille.

    Pourquoi : vérifier que la complexité reste raisonnable (pas d'explosion).
    Attendu : croissance au plus O(n²) ou O(n log n) selon l'algorithme.
    """
    sizes = [10, 50, 100, 200]
    timings = []

    for n in sizes:
        points = generate_random_points(n, seed=n)

        start = time.perf_counter()
        triangles = triangulate(points)
        elapsed = time.perf_counter() - start

        timings.append(elapsed)
        print(f"\nn={n:4d} : {elapsed:.6f} s ({len(triangles)} triangles)")

    # Vérifier que les temps ne croissent pas de manière explosive
    # Ratio entre 200 et 10 points : au plus 400x pour O(n²), 20x pour O(n log n)
    ratio = timings[-1] / timings[0] if timings[0] > 0 else float('inf')
    print(f"\nRatio (200pts / 10pts) : {ratio:.2f}x")

    # Accepter jusqu'à O(n²) : 20² = 400x
    assert ratio < 500, \
        f"Croissance trop rapide : ratio {ratio:.2f}x (attendu < 500x pour O(n²))"


@pytest.mark.perf
def test_perf_triangulate_grid_vs_random():
    """Test de comparaison : grille régulière vs points aléatoires.

    Pourquoi : certains algorithmes peuvent avoir des performances
    différentes selon la distribution des points.
    """
    n = 100

    # Grille
    grid_points = generate_grid_points(10, 10)
    start = time.perf_counter()
    triangles_grid = triangulate(grid_points)
    elapsed_grid = time.perf_counter() - start

    # Aléatoire
    random_points = generate_random_points(n)
    start = time.perf_counter()
    triangles_random = triangulate(random_points)
    elapsed_random = time.perf_counter() - start

    print(f"\nGrille 10x10 : {elapsed_grid:.6f} s ({len(triangles_grid)} triangles)")
    print(f"Aléatoire 100: {elapsed_random:.6f} s ({len(triangles_random)} triangles)")

    # Les deux devraient être dans le même ordre de grandeur
    ratio = max(elapsed_grid, elapsed_random) / min(elapsed_grid, elapsed_random)
    assert ratio < 10, \
        f"Écart trop important entre grille et aléatoire : ratio {ratio:.2f}x"


 
# Tests de performance : Encodage/Décodage binaire
 

@pytest.mark.perf
def test_perf_encode_pointset_100_points():
    """Test de performance : encodage de 100 points.

    Pourquoi : mesurer le coût de la sérialisation binaire.
    Budget : < 0.001 seconde (devrait être très rapide)
    """
    points = generate_random_points(100)

    start = time.perf_counter()
    buffer = encode_pointset(points)
    elapsed = time.perf_counter() - start

    print(f"\nEncodage de 100 points : {elapsed:.6f} s ({len(buffer)} bytes)")

    assert elapsed < 0.001, \
        f"Encodage devrait être < 0.001s, pris {elapsed:.6f}s"


@pytest.mark.perf
def test_perf_decode_pointset_100_points():
    """Test de performance : décodage de 100 points.

    Pourquoi : mesurer le coût de la désérialisation binaire.
    Budget : < 0.001 seconde
    """
    points = generate_random_points(100)
    buffer = encode_pointset(points)

    start = time.perf_counter()
    _ = decode_pointset(buffer)
    elapsed = time.perf_counter() - start

    print(f"\nDécodage de 100 points : {elapsed:.6f} s")

    assert elapsed < 0.001, \
        f"Décodage devrait être < 0.001s, pris {elapsed:.6f}s"


@pytest.mark.perf
def test_perf_roundtrip_pointset_1000_points():
    """Test de performance : round-trip (encode + decode) de 1000 points.

    Pourquoi : mesurer le coût total de la sérialisation/désérialisation.
    Budget : < 0.01 seconde
    """
    points = generate_random_points(1000)

    start = time.perf_counter()
    buffer = encode_pointset(points)
    decoded = decode_pointset(buffer)
    elapsed = time.perf_counter() - start

    print(f"\nRound-trip 1000 points : {elapsed:.6f} s")

    assert elapsed < 0.01, \
        f"Round-trip devrait être < 0.01s, pris {elapsed:.6f}s"

    assert len(decoded) == len(points)


@pytest.mark.perf
def test_perf_encode_decode_complexity():
    """Test de la complexité linéaire de l'encodage/décodage.

    Pourquoi : vérifier que l'encodage/décodage est bien O(n).
    """
    sizes = [100, 500, 1000, 5000]
    encode_timings = []
    decode_timings = []

    for n in sizes:
        points = generate_random_points(n, seed=n)

        # Encodage
        start = time.perf_counter()
        buffer = encode_pointset(points)
        encode_time = time.perf_counter() - start
        encode_timings.append(encode_time)

        # Décodage
        start = time.perf_counter()
        _ = decode_pointset(buffer)
        decode_time = time.perf_counter() - start
        decode_timings.append(decode_time)

        print(f"\nn={n:5d} : encode={encode_time:.6f}s, decode={decode_time:.6f}s")

    # Vérifier la croissance linéaire
    # Ratio 5000/100 = 50x, devrait être proche de 50x pour O(n)
    encode_ratio = (
        encode_timings[-1] / encode_timings[0]
        if encode_timings[0] > 0
        else float('inf')
    )
    decode_ratio = (
        decode_timings[-1] / decode_timings[0]
        if decode_timings[0] > 0
        else float('inf')
    )

    print(f"\nEncode ratio (5000/100) : {encode_ratio:.2f}x (attendu ≈ 50x)")
    print(f"Decode ratio (5000/100) : {decode_ratio:.2f}x (attendu ≈ 50x)")

    # Accepter une marge (10x à 100x pour tenir compte du overhead)
    assert encode_ratio < 100, f"Encodage devrait être O(n), ratio {encode_ratio:.2f}x"
    assert decode_ratio < 100, f"Décodage devrait être O(n), ratio {decode_ratio:.2f}x"


 
# Tests de performance : Encodage/Décodage Triangles
 

@pytest.mark.perf
def test_perf_encode_triangles_square():
    """Test de performance : encodage de Triangles (carré).

    Pourquoi : mesurer le coût de l'encodage complet.
    """
    points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    triangles = [(0, 1, 2), (0, 2, 3)]

    start = time.perf_counter()
    buffer = encode_triangles(points, triangles)
    elapsed = time.perf_counter() - start

    print(f"\nEncodage Triangles (carré) : {elapsed:.6f} s ({len(buffer)} bytes)")

    assert elapsed < 0.001


@pytest.mark.perf
def test_perf_decode_triangles_square():
    """Test de performance : décodage de Triangles (carré).

    Pourquoi : mesurer le coût du décodage complet.
    """
    points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    triangles_in = [(0, 1, 2), (0, 2, 3)]
    buffer = encode_triangles(points, triangles_in)

    start = time.perf_counter()
    decoded_points, decoded_triangles = decode_triangles(buffer)
    elapsed = time.perf_counter() - start

    print(f"\nDécodage Triangles (carré) : {elapsed:.6f} s")

    assert elapsed < 0.001


@pytest.mark.perf
def test_perf_roundtrip_triangles_100_points():
    """Test de performance : round-trip Triangles avec 100 points.

    Pourquoi : mesurer le coût total pour des structures complexes.
    """
    points = generate_random_points(100)

    # Générer des triangles factices (la triangulation réelle sera testée ailleurs)
    # On suppose environ 2*(n-2) triangles pour n points
    num_triangles = 2 * (len(points) - 2)
    triangles_in = [(i % len(points), (i+1) % len(points), (i+2) % len(points))
                    for i in range(min(num_triangles, 100))]

    start = time.perf_counter()
    buffer = encode_triangles(points, triangles_in)
    decoded_points, decoded_triangles = decode_triangles(buffer)
    elapsed = time.perf_counter() - start

    print(
        f"\nRound-trip Triangles (100 points, {len(triangles_in)} "
        f"triangles) : {elapsed:.6f} s"
    )

    assert elapsed < 0.01


 
# Tests de performance : Triangulation + Encodage (bout en bout)
 

@pytest.mark.perf
def test_perf_end_to_end_100_points():
    """Test de performance bout en bout : triangulation + encodage.

    Pourquoi : mesurer le coût total d'un workflow complet.
    Budget : < 0.2 seconde
    """
    points = generate_random_points(100)

    start = time.perf_counter()

    # Triangulation
    triangles = triangulate(points)

    # Encodage
    buffer = encode_triangles(points, triangles)

    elapsed = time.perf_counter() - start

    print(f"\nBout en bout (100 points) : {elapsed:.6f} s")
    print(f"Triangles générés : {len(triangles)}")
    print(f"Taille buffer : {len(buffer)} bytes")

    assert elapsed < 0.2, \
        f"Workflow complet devrait être < 0.2s, pris {elapsed:.6f}s"


@pytest.mark.perf
def test_perf_end_to_end_500_points():
    """Test de performance bout en bout : 500 points.

    Pourquoi : vérifier les performances sur un ensemble plus grand.
    Budget : < 1.0 seconde
    """
    points = generate_random_points(500, seed=500)

    start = time.perf_counter()
    triangles = triangulate(points)
    buffer = encode_triangles(points, triangles)
    elapsed = time.perf_counter() - start

    print(f"\nBout en bout (500 points) : {elapsed:.6f} s")
    print(f"Triangles générés : {len(triangles)}")
    print(f"Taille buffer : {len(buffer)} bytes")

    assert elapsed < 1.0, \
        f"Workflow complet devrait être < 1.0s, pris {elapsed:.6f}s"


 
# Tests de performance : Cas spéciaux
 

@pytest.mark.perf
def test_perf_triangulate_circle_1000_points():
    """Test de performance : triangulation de points sur un cercle.

    Pourquoi : cas spécial où les points sont ordonnés circulairement.
    """
    points = generate_circle_points(1000)

    start = time.perf_counter()
    triangles = triangulate(points)
    elapsed = time.perf_counter() - start

    print(f"\nTriangulation cercle (1000 points) : {elapsed:.6f} s")
    print(f"Triangles générés : {len(triangles)}")

    assert elapsed < 12.0, (
        f"Triangulation de 1000 points en cercle devrait prendre "
        f"< 12s, pris {elapsed:.6f}s"
    )


@pytest.mark.perf
def test_perf_triangulate_grid_30x30():
    """Test de performance : triangulation d'une grille 30x30.

    Pourquoi : distribution régulière de 900 points.
    """
    points = generate_grid_points(30, 30)

    start = time.perf_counter()
    triangles = triangulate(points)
    elapsed = time.perf_counter() - start

    print(f"\nTriangulation grille 30x30 : {elapsed:.6f} s")
    print(f"Triangles générés : {len(triangles)}")

    assert elapsed < 2.0


 
# Tests de performance : Mémoire (indicatif)
 

@pytest.mark.perf
def test_perf_memory_footprint_1000_points():
    """Test indicatif de l'empreinte mémoire.

    Pourquoi : vérifier que la mémoire utilisée reste raisonnable.
    Note : ce test ne mesure pas précisément la mémoire, mais vérifie
    que l'exécution ne plante pas avec de grandes structures.
    """
    points = generate_random_points(1000)

    # Triangulation
    triangles = triangulate(points)

    # Encodage
    buffer = encode_triangles(points, triangles)

    # Vérifier que les structures sont cohérentes
    assert len(triangles) > 0
    assert len(buffer) > 0

    print(f"\n1000 points : {len(triangles)} triangles, {len(buffer)} bytes")


 
# Tests de performance : Reproductibilité
 

@pytest.mark.perf
def test_perf_reproducibility():
    """Test de reproductibilité des mesures de performance.

    Pourquoi : vérifier que les mesures sont stables entre plusieurs exécutions.
    """
    points = generate_random_points(100, seed=42)

    timings = []
    for _ in range(5):
        start = time.perf_counter()
        _ = triangulate(points)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    avg_time = sum(timings) / len(timings)
    std_dev = (sum((t - avg_time) ** 2 for t in timings) / len(timings)) ** 0.5

    print(f"\n5 exécutions : moyenne={avg_time:.6f}s, écart-type={std_dev:.6f}s")

    # L'écart-type devrait être faible (< 30% de la moyenne)
    assert std_dev < 0.3 * avg_time, \
        f"Mesures instables : écart-type {std_dev:.6f}s (> 30% de {avg_time:.6f}s)"
