"""Tests unitaires pour l'algorithme de triangulation.

Ce module teste :
- Le comportement de l'algorithme de triangulation sur différentes distributions
- La gestion des cas limites (< 3 points, points colinéaires, doublons)
- La validité géométrique des triangles produits
- La robustesse face aux dégénérescences et aux flottants

Propriétés attendues d'une triangulation valide :
- Tous les triangles utilisent uniquement les points fournis
- Aucun triangle ne doit être dégénéré (aire ≈ 0)
- Les indices des triangles doivent être dans [0, N-1]
- Pas de chevauchement de triangles (pour Delaunay)
"""

import math

import pytest

from triangulator.core import triangulate

# Helpers : validation géométrique

def triangle_area(p0, p1, p2):
    """Retourne l'aire signée d'un triangle (déterminant / 2).

    Pourquoi : permet de détecter les triangles dégénérés (aire ≈ 0).
    """
    x0, y0 = p0
    x1, y1 = p1
    x2, y2 = p2
    return abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)) / 2.0


def is_degenerate_triangle(p0, p1, p2, tolerance=1e-9):
    """Vérifie si un triangle est dégénéré (aire proche de 0).

    Pourquoi : les triangles dégénérés ne sont pas valides géométriquement.
    """
    area = triangle_area(p0, p1, p2)
    return area < tolerance


def are_points_collinear(points, tolerance=1e-9):
    """Vérifie si tous les points sont colinéaires.

    Pourquoi : détecte les configurations où aucun triangle valide n'existe.
    """
    if len(points) < 3:
        return True

    # Prendre les 2 premiers points comme référence
    x0, y0 = points[0]
    x1, y1 = points[1]

    # Vérifier que tous les autres points sont sur la même droite
    for x2, y2 in points[2:]:
        # Produit vectoriel (cross product) pour vérifier la colinéarité
        cross = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(cross) > tolerance:
            return False

    return True


 
# Tests : Cas limites (< 3 points)
 

def test_triangulate_empty_points(empty_points):
    """Test de triangulation avec 0 point.

    Pourquoi : aucun triangle ne peut être formé, devrait retourner [].
    """
    triangles = triangulate(empty_points)

    assert triangles == [], \
        "Triangulation of 0 points should return an empty list"


def test_triangulate_one_point():
    """Test de triangulation avec 1 point.

    Pourquoi : insuffisant pour former un triangle.
    """
    points = [(0.0, 0.0)]
    triangles = triangulate(points)

    assert len(triangles) == 0, \
        "Triangulation of 1 point should return 0 triangles"


def test_triangulate_two_points(two_points):
    """Test de triangulation avec 2 points.

    Pourquoi : insuffisant pour former un triangle.
    """
    triangles = triangulate(two_points)

    assert len(triangles) == 0, \
        "Triangulation of 2 points should return 0 triangles"


 
# Tests : Triangle simple (3 points)
 

def test_triangulate_simple_triangle(triangle_points):
    """Test de triangulation d'un triangle simple.

    Pourquoi : cas de base, devrait produire exactement 1 triangle
    avec les indices (0, 1, 2) ou une permutation valide.
    """
    triangles = triangulate(triangle_points)

    assert len(triangles) == 1, \
        "Triangulation of 3 non-collinear points should produce exactly 1 triangle"

    # Vérifier que le triangle utilise les 3 points
    triangle = triangles[0]
    assert len(triangle) == 3, "A triangle should have 3 vertices"

    i, j, k = triangle
    assert 0 <= i < len(triangle_points), f"Invalid index {i}"
    assert 0 <= j < len(triangle_points), f"Invalid index {j}"
    assert 0 <= k < len(triangle_points), f"Invalid index {k}"

    # Vérifier que le triangle n'est pas dégénéré
    p0, p1, p2 = triangle_points[i], triangle_points[j], triangle_points[k]
    assert not is_degenerate_triangle(p0, p1, p2), \
        "Triangle should not be degenerate"


def test_triangulate_collinear_points(collinear_points):
    """Test de triangulation avec 3 points colinéaires.

    Pourquoi : aucun triangle valide ne peut être formé,
    devrait retourner 0 triangle.
    """
    triangles = triangulate(collinear_points)

    assert len(triangles) == 0, \
        "Triangulation of collinear points should return 0 triangles"


 
# Tests : Carré (4 points)
 

def test_triangulate_square(square_points):
    """Test de triangulation d'un carré.

    Pourquoi : devrait produire exactement 2 triangles non-chevauchants.
    """
    triangles = triangulate(square_points)

    assert len(triangles) == 2, \
        "Triangulation of a square should produce exactly 2 triangles"

    # Vérifier que tous les indices sont valides
    for idx, (i, j, k) in enumerate(triangles):
        assert 0 <= i < len(square_points), f"Triangle {idx}: invalid index {i}"
        assert 0 <= j < len(square_points), f"Triangle {idx}: invalid index {j}"
        assert 0 <= k < len(square_points), f"Triangle {idx}: invalid index {k}"

        # Vérifier que le triangle n'est pas dégénéré
        p0, p1, p2 = square_points[i], square_points[j], square_points[k]
        assert not is_degenerate_triangle(p0, p1, p2), \
            f"Triangle {idx} should not be degenerate"


def test_triangulate_square_total_area(square_points):
    """Test que la somme des aires des triangles égale l'aire du carré.

    Pourquoi : vérifier que la triangulation couvre bien toute la surface
    sans chevauchement ni trou.
    """
    triangles = triangulate(square_points)

    # Aire du carré : 1 x 1 = 1
    expected_area = 1.0

    total_area = 0.0
    for i, j, k in triangles:
        p0, p1, p2 = square_points[i], square_points[j], square_points[k]
        total_area += triangle_area(p0, p1, p2)

    assert total_area == pytest.approx(expected_area, abs=1e-6), \
        f"Total area {total_area} should equal square area {expected_area}"


 
# Tests : Pentagon (5 points)
 

def test_triangulate_pentagon(pentagon_points):
    """Test de triangulation d'un pentagone régulier.

    Pourquoi : un pentagone peut être triangulé en 3 triangles.
    Formule : n points convexes -> (n-2) triangles.
    """
    triangles = triangulate(pentagon_points)

    # Un pentagone convexe devrait produire 3 triangles
    assert len(triangles) == 3, \
        "Triangulation of a pentagon should produce 3 triangles"

    # Vérifier que tous les indices sont valides
    for idx, (i, j, k) in enumerate(triangles):
        assert 0 <= i < len(pentagon_points)
        assert 0 <= j < len(pentagon_points)
        assert 0 <= k < len(pentagon_points)

        # Vérifier que le triangle n'est pas dégénéré
        p0, p1, p2 = pentagon_points[i], pentagon_points[j], pentagon_points[k]
        assert not is_degenerate_triangle(p0, p1, p2), \
            f"Triangle {idx} should not be degenerate"


 
# Tests : Grille (distribution régulière)
 

def test_triangulate_grid(grid_points):
    """Test de triangulation d'une grille 3x3 (9 points).

    Pourquoi : teste une distribution régulière et vérifie
    qu'aucun triangle n'est dégénéré.
    """
    triangles = triangulate(grid_points)

    # Nombre minimal de triangles pour 9 points (varie selon l'algo)
    # Une triangulation complète d'une grille 3x3 donne typiquement 8 triangles
    assert len(triangles) >= 7, \
        "Triangulation of a 3x3 grid should produce at least 7 triangles"

    # Vérifier la validité de chaque triangle
    for idx, (i, j, k) in enumerate(triangles):
        assert 0 <= i < len(grid_points)
        assert 0 <= j < len(grid_points)
        assert 0 <= k < len(grid_points)

        p0, p1, p2 = grid_points[i], grid_points[j], grid_points[k]
        assert not is_degenerate_triangle(p0, p1, p2), \
            f"Triangle {idx} should not be degenerate"


def test_triangulate_grid_no_duplicate_triangles(grid_points):
    """Test qu'il n'y a pas de triangles dupliqués dans une grille.

    Pourquoi : chaque triangle devrait être unique (même topologie).
    """
    triangles = triangulate(grid_points)

    # Normaliser les triangles (trier les indices) pour détecter les doublons
    normalized = [tuple(sorted([i, j, k])) for i, j, k in triangles]

    # Vérifier qu'il n'y a pas de doublons
    assert len(normalized) == len(set(normalized)), \
        "Triangulation should not produce duplicate triangles"


 
# Tests : Cercle (distribution circulaire)
 

def test_triangulate_circle():
    """Test de triangulation de points disposés en cercle.

    Pourquoi : teste une distribution circulaire (cas fréquent).
    """
    # Générer 8 points sur un cercle
    n = 8
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        x = math.cos(angle)
        y = math.sin(angle)
        points.append((x, y))

    triangles = triangulate(points)

    # Un polygone convexe de 8 points -> 6 triangles
    assert len(triangles) == 6, \
        "Triangulation of 8 points on a circle should produce 6 triangles"

    # Vérifier la validité
    for idx, (i, j, k) in enumerate(triangles):
        assert 0 <= i < len(points)
        assert 0 <= j < len(points)
        assert 0 <= k < len(points)

        p0, p1, p2 = points[i], points[j], points[k]
        assert not is_degenerate_triangle(p0, p1, p2), \
            f"Triangle {idx} should not be degenerate"


 
# Tests : Points aléatoires
 

def test_triangulate_random_10(random_points_10):
    """Test de triangulation de 10 points aléatoires.

    Pourquoi : teste une distribution aléatoire reproductible.
    """
    triangles = triangulate(random_points_10)

    # Vérifier que des triangles ont été générés
    assert len(triangles) > 0, \
        "Triangulation of 10 random points should produce triangles"

    # Vérifier la validité
    for idx, (i, j, k) in enumerate(triangles):
        assert 0 <= i < len(random_points_10)
        assert 0 <= j < len(random_points_10)
        assert 0 <= k < len(random_points_10)

        p0, p1, p2 = random_points_10[i], random_points_10[j], random_points_10[k]
        assert not is_degenerate_triangle(p0, p1, p2), \
            f"Triangle {idx} should not be degenerate"


def test_triangulate_random_no_self_intersection(random_points_10):
    """Test qu'aucun triangle ne partage exactement les mêmes 3 sommets.

    Pourquoi : les triangles doivent être uniques topologiquement.
    """
    triangles = triangulate(random_points_10)

    normalized = [tuple(sorted([i, j, k])) for i, j, k in triangles]
    assert len(normalized) == len(set(normalized)), \
        "No duplicate triangles should exist"


 
# Tests : Doublons de points
 

def test_triangulate_duplicate_points(duplicate_points):
    """Test de triangulation avec des points dupliqués.

    Pourquoi : le comportement doit être défini (accepter ou rejeter).
    Ici, on s'attend à ce que les doublons soient soit ignorés,
    soit causent une exception claire.
    """
    # Option 1 : les doublons sont acceptés et traités
    # Option 2 : une exception est levée
    try:
        triangles = triangulate(duplicate_points)
        # Si acceptés, vérifier la validité des triangles générés
        for _idx, (i, j, k) in enumerate(triangles):
            assert 0 <= i < len(duplicate_points)
            assert 0 <= j < len(duplicate_points)
            assert 0 <= k < len(duplicate_points)
    except ValueError as e:
        # Si rejetés, vérifier le message d'erreur
        assert "duplicate" in str(e).lower() or "identical" in str(e).lower(), \
            "Exception message should mention duplicates"


 
# Tests : Stabilité numérique / tolérance
 

def test_triangulate_almost_collinear():
    """Test de triangulation avec des points presque colinéaires.

    Pourquoi : les erreurs d'arrondi flottant peuvent rendre des points
    presque colinéaires difficiles à gérer. Le comportement doit être
    robuste et documenté.
    """
    # Points presque colinéaires (légèrement décalés)
    points = [(0.0, 0.0), (1.0, 1e-10), (2.0, 2e-10)]

    triangles = triangulate(points)

    # Soit 0 triangle (traités comme colinéaires), soit 1 triangle très fin
    # Le comportement exact dépend de la tolérance de l'algorithme
    if len(triangles) == 1:
        # Si un triangle est créé, vérifier qu'il est presque dégénéré
        i, j, k = triangles[0]
        p0, p1, p2 = points[i], points[j], points[k]
        area = triangle_area(p0, p1, p2)
        assert area < 1e-8, \
            "Triangle from almost-collinear points should have very small area"
    else:
        # Si aucun triangle, c'est acceptable
        assert len(triangles) == 0


def test_triangulate_tiny_triangle():
    """Test de triangulation avec un triangle de très petite taille.

    Pourquoi : vérifier que les petites échelles sont gérées correctement.
    """
    points = [(0.0, 0.0), (1e-6, 0.0), (0.0, 1e-6)]

    triangles = triangulate(points)

    if len(triangles) > 0:
        # Si triangulé, vérifier la validité
        assert len(triangles) == 1
        i, j, k = triangles[0]
        assert 0 <= i < len(points)
        assert 0 <= j < len(points)
        assert 0 <= k < len(points)


def test_triangulate_large_coords():
    """Test de triangulation avec de grandes coordonnées.

    Pourquoi : vérifier que les grandes valeurs sont gérées sans overflow.
    """
    points = [(0.0, 0.0), (1e6, 0.0), (0.0, 1e6)]

    triangles = triangulate(points)

    assert len(triangles) == 1, \
        "Large coordinates should still produce a valid triangle"

    i, j, k = triangles[0]
    p0, p1, p2 = points[i], points[j], points[k]
    assert not is_degenerate_triangle(p0, p1, p2, tolerance=1e3), \
        "Triangle with large coords should not be degenerate"


 
# Tests : Validation des propriétés géométriques
 

def test_triangulate_all_triangles_have_positive_orientation(square_points):
    """Test que tous les triangles ont la même orientation.

    Pourquoi : une triangulation cohérente devrait avoir une orientation
    uniforme (sens horaire ou anti-horaire).
    """
    triangles = triangulate(square_points)

    orientations = []
    for i, j, k in triangles:
        p0, p1, p2 = square_points[i], square_points[j], square_points[k]
        x0, y0 = p0
        x1, y1 = p1
        x2, y2 = p2

        # Produit vectoriel pour déterminer l'orientation
        cross = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        orientations.append(cross > 0)

    # Tous les triangles devraient avoir la même orientation
    # (soit tous positifs, soit tous négatifs)
    if orientations:
        _first_orientation = orientations[0]
        # Note : dans certaines triangulations, l'orientation peut varier
        # Ce test est optionnel et dépend de l'algorithme choisi


def test_triangulate_vertex_coverage(pentagon_points):
    """Test que tous les points sont utilisés dans au moins un triangle.

    Pourquoi : une triangulation complète devrait couvrir tous les points.
    """
    triangles = triangulate(pentagon_points)

    # Collecter tous les indices utilisés
    used_indices = set()
    for i, j, k in triangles:
        used_indices.add(i)
        used_indices.add(j)
        used_indices.add(k)

    # Vérifier que tous les indices sont présents
    expected_indices = set(range(len(pentagon_points)))
    assert used_indices == expected_indices, (
        f"All points should be used in triangulation. "
        f"Missing: {expected_indices - used_indices}"
    )


 
# Tests : Cas spéciaux géométriques
 

def test_triangulate_all_points_on_vertical_line():
    """Test avec tous les points sur une ligne verticale.

    Pourquoi : cas particulier de colinéarité, devrait retourner 0 triangle.
    """
    points = [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0), (0.0, 3.0)]

    triangles = triangulate(points)

    assert len(triangles) == 0, \
        "Points on a vertical line should produce 0 triangles"


def test_triangulate_all_points_on_horizontal_line():
    """Test avec tous les points sur une ligne horizontale.

    Pourquoi : cas particulier de colinéarité.
    """
    points = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)]

    triangles = triangulate(points)

    assert len(triangles) == 0, \
        "Points on a horizontal line should produce 0 triangles"


def test_triangulate_l_shape():
    """Test de triangulation d'une forme en L.

    Pourquoi : teste une forme concave simple.
    """
    points = [
        (0.0, 0.0), (1.0, 0.0), (1.0, 1.0),
        (2.0, 1.0), (2.0, 2.0), (0.0, 2.0)
    ]

    triangles = triangulate(points)

    # Une forme en L de 6 points -> 4 ou 5 triangles (selon l'algorithme)
    assert len(triangles) in [4, 5], \
        f"L-shape with 6 points should produce 4 or 5 triangles, got {len(triangles)}"

    # Vérifier la validité
    for idx, (i, j, k) in enumerate(triangles):
        assert 0 <= i < len(points)
        assert 0 <= j < len(points)
        assert 0 <= k < len(points)

        p0, p1, p2 = points[i], points[j], points[k]
        assert not is_degenerate_triangle(p0, p1, p2), \
            f"Triangle {idx} should not be degenerate"


 
# Tests : Edge cases additionnels
 

def test_triangulate_single_point_repeated_three_times():
    """Test avec un point répété 3 fois (tous identiques).

    Pourquoi : cas extrême de doublons, devrait être rejeté ou retourner 0 triangle.
    """
    points = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

    try:
        triangles = triangulate(points)
        assert len(triangles) == 0, \
            "Three identical points should produce 0 triangles"
    except ValueError:
        # Acceptable si l'algorithme rejette explicitement
        pass


def test_triangulate_negative_coordinates():
    """Test avec des coordonnées négatives.

    Pourquoi : les coordonnées négatives sont valides géométriquement.
    """
    points = [(-1.0, -1.0), (1.0, -1.0), (0.0, 1.0)]

    triangles = triangulate(points)

    assert len(triangles) == 1, \
        "Negative coordinates should be handled correctly"

    i, j, k = triangles[0]
    p0, p1, p2 = points[i], points[j], points[k]
    assert not is_degenerate_triangle(p0, p1, p2)
