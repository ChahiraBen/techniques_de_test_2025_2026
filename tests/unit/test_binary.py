"""Tests unitaires pour la sérialisation/désérialisation binaire.

Ce module teste :
- Le décodage de PointSet depuis le format binaire
- L'encodage de PointSet vers le format binaire
- Le décodage de Triangles depuis le format binaire
- L'encodage de Triangles vers le format binaire
- La gestion des cas d'erreur (données tronquées, indices invalides, etc.)
- Les round-trips (encode -> decode -> égalité)

Format binaire PointSet (little-endian) :
    - 4 bytes : unsigned long (nombre de points)
    - N * 8 bytes : N points, chaque point = 2 floats (X, Y)

Format binaire Triangles (little-endian) :
    - PointSet (voir ci-dessus)
    - 4 bytes : unsigned long (nombre de triangles)
    - T * 12 bytes : T triangles, chaque triangle = 3 unsigned long (indices)
"""

import struct
import pytest
import math
from triangulator.binary import (
    decode_pointset,
    encode_pointset,
    decode_triangles,
    encode_triangles,
)


#Test décodage PointSet: 

def test_decode_valid_pointset(valid_pointset_binary, triangle_points):
    """Test du décodage d'un PointSet valide
    Pourquoi : vérifier que l'interprétation du format binaire est correcte
    et que les coordonnées sont restaurées exactement
    """
    points = decode_pointset(valid_pointset_binary)

    assert len(points) == len(triangle_points), \
        f"Expected {len(triangle_points)} points, got {len(points)}"

    for i, ((x_expected, y_expected), (x_actual, y_actual)) in enumerate(
        zip(triangle_points, points)
    ):
        assert x_actual == pytest.approx(x_expected, abs=1e-6), \
            f"Point {i}: X coordinate mismatch"
        assert y_actual == pytest.approx(y_expected, abs=1e-6), \
            f"Point {i}: Y coordinate mismatch"


def test_decode_empty_pointset(empty_pointset_binary):
    """Test du décodage d'un PointSet vide (0 point).

    Pourquoi : cas limite valide, doit être géré sans erreur.
    """
    points = decode_pointset(empty_pointset_binary)

    assert len(points) == 0, \
        "Empty PointSet should decode to an empty list"


def test_decode_truncated_pointset(truncated_pointset_binary):
    """Test du décodage d'un PointSet tronqué.

    Pourquoi : les données incomplètes doivent être rejetées avec
    une exception explicite pour éviter les comportements silencieux.
    """
    with pytest.raises(ValueError, match="truncated|incomplete|insufficient"):
        decode_pointset(truncated_pointset_binary)


def test_decode_malformed_pointset(malformed_pointset_binary):
    """Test du décodage d'un buffer trop court.

    Pourquoi : un buffer qui ne contient même pas le count complet
    doit être rejeté immédiatement.
    """
    with pytest.raises((ValueError, struct.error)):
        decode_pointset(malformed_pointset_binary)


def test_decode_pointset_with_nan(pointset_with_nan):
    """Test du décodage d'un PointSet contenant des NaN.

    Pourquoi : les valeurs NaN ne sont pas des coordonnées valides,
    elles doivent être rejetées explicitement.
    """
    with pytest.raises(ValueError, match="NaN|invalid"):
        decode_pointset(pointset_with_nan)


def test_decode_pointset_with_inf(pointset_with_inf):
    """Test du décodage d'un PointSet contenant des Inf.

    Pourquoi : les valeurs infinies ne sont pas géométriquement valides.
    """
    with pytest.raises(ValueError, match="inf|invalid"):
        decode_pointset(pointset_with_inf)


def test_decode_square_pointset(square_points):
    """Test du décodage d'un carré.

    Pourquoi : vérifier avec un cas simple et régulier de 4 points.
    """
    # Encoder manuellement
    buffer = struct.pack('<I', len(square_points))
    for x, y in square_points:
        buffer += struct.pack('<ff', x, y)

    # Décoder
    points = decode_pointset(buffer)

    assert len(points) == 4
    for i, ((x_exp, y_exp), (x_act, y_act)) in enumerate(
        zip(square_points, points)
    ):
        assert x_act == pytest.approx(x_exp), f"Point {i} X mismatch"
        assert y_act == pytest.approx(y_exp), f"Point {i} Y mismatch"


# Tests: Encodage PointSet

def test_encode_valid_pointset(triangle_points):
    """Test de l'encodage d'un PointSet valide.

    Pourquoi: vérifier que la structure binaire générée respecte
    le format attendu (count + coordonnées).
    """
    buffer = encode_pointset(triangle_points)

    # Vérifier la taille : 4 bytes (count) + 3 * 8 bytes (3 points)
    expected_size = 4 + len(triangle_points) * 8
    assert len(buffer) == expected_size, \
        f"Expected buffer size {expected_size}, got {len(buffer)}"

    # Vérifier le count
    count = struct.unpack('<I', buffer[:4])[0]
    assert count == len(triangle_points), \
        f"Expected count {len(triangle_points)}, got {count}"

    # Vérifier les coordonnées
    offset = 4
    for i, (x_exp, y_exp) in enumerate(triangle_points):
        x, y = struct.unpack('<ff', buffer[offset:offset+8])
        assert x == pytest.approx(x_exp), f"Point {i} X encoding error"
        assert y == pytest.approx(y_exp), f"Point {i} Y encoding error"
        offset += 8


def test_encode_empty_pointset(empty_points):
    """Test de l'encodage d'un PointSet vide.

    Pourquoi : le cas limite de 0 point doit être encodé correctement.
    """
    buffer = encode_pointset(empty_points)

    assert len(buffer) == 4, "Empty PointSet should encode to 4 bytes (count=0)"

    count = struct.unpack('<I', buffer)[0]
    assert count == 0, "Count should be 0 for empty PointSet"


def test_encode_pointset_with_duplicates(duplicate_points):
    """Test de l'encodage d'un PointSet avec doublons.

    Pourquoi : vérifier que les doublons sont encodés tels quels
    (la validation se fera au niveau de la triangulation).
    """
    buffer = encode_pointset(duplicate_points)

    # Devrait encoder tous les points, même les doublons
    expected_size = 4 + len(duplicate_points) * 8
    assert len(buffer) == expected_size


def test_encode_pointset_with_negative_coords():
    """Test de l'encodage avec des coordonnées négatives.

    Pourquoi : les coordonnées négatives sont géométriquement valides.
    """
    points = [(-1.0, -1.0), (-2.5, 3.7), (0.0, -5.0)]
    buffer = encode_pointset(points)

    assert len(buffer) == 4 + len(points) * 8

    # Vérifier le décodage pour confirmer
    decoded = decode_pointset(buffer)
    for (x_exp, y_exp), (x_act, y_act) in zip(points, decoded):
        assert x_act == pytest.approx(x_exp)
        assert y_act == pytest.approx(y_exp)


def test_encode_pointset_with_large_coords():
    """Test de l'encodage avec de grandes coordonnées.

    Pourquoi : vérifier que les floats larges sont gérés correctement.
    """
    points = [(1e6, 1e6), (-1e6, -1e6), (1e-6, 1e-6)]
    buffer = encode_pointset(points)

    decoded = decode_pointset(buffer)
    for (x_exp, y_exp), (x_act, y_act) in zip(points, decoded):
        # Tolérance relative pour les grandes valeurs
        assert x_act == pytest.approx(x_exp, rel=1e-5)
        assert y_act == pytest.approx(y_exp, rel=1e-5)


# Tests : Round-trip PointSet (encode -> decode -> égalité)

def test_roundtrip_pointset_triangle(triangle_points):
    """Test round-trip PointSet : encode -> decode -> égalité (triangle).

    Pourquoi : vérifier la cohérence complète de l'encodage/décodage.
    """
    buffer = encode_pointset(triangle_points)
    decoded = decode_pointset(buffer)

    assert len(decoded) == len(triangle_points)
    for (x_exp, y_exp), (x_act, y_act) in zip(triangle_points, decoded):
        assert x_act == pytest.approx(x_exp)
        assert y_act == pytest.approx(y_exp)


def test_roundtrip_pointset_square(square_points):
    """Test round-trip PointSet : encode -> decode -> égalité (carré).

    Pourquoi : vérifier avec un cas à 4 points.
    """
    buffer = encode_pointset(square_points)
    decoded = decode_pointset(buffer)

    assert len(decoded) == len(square_points)
    for (x_exp, y_exp), (x_act, y_act) in zip(square_points, decoded):
        assert x_act == pytest.approx(x_exp)
        assert y_act == pytest.approx(y_exp)


def test_roundtrip_pointset_grid(grid_points):
    """Test round-trip PointSet : encode -> decode -> égalité (grille 3x3).

    Pourquoi : vérifier avec un cas plus grand (9 points).
    """
    buffer = encode_pointset(grid_points)
    decoded = decode_pointset(buffer)

    assert len(decoded) == len(grid_points)
    for (x_exp, y_exp), (x_act, y_act) in zip(grid_points, decoded):
        assert x_act == pytest.approx(x_exp)
        assert y_act == pytest.approx(y_exp)


# Tests : Décodage Triangles


def test_decode_valid_triangles(valid_triangles_binary, square_points):
    """Test du décodage de Triangles valides (carré -> 2 triangles).

    Pourquoi : vérifier que la structure Triangles complète est
    correctement décodée (points + triangles).
    """
    points, triangles = decode_triangles(valid_triangles_binary)

    # Vérifier les points
    assert len(points) == len(square_points), \
        f"Expected {len(square_points)} points, got {len(points)}"

    for (x_exp, y_exp), (x_act, y_act) in zip(square_points, points):
        assert x_act == pytest.approx(x_exp)
        assert y_act == pytest.approx(y_exp)

    # Vérifier les triangles
    assert len(triangles) == 2, "Expected 2 triangles for a square"

    # Chaque triangle doit avoir 3 indices valides
    for i, (idx0, idx1, idx2) in enumerate(triangles):
        assert 0 <= idx0 < len(points), f"Triangle {i}: invalid index {idx0}"
        assert 0 <= idx1 < len(points), f"Triangle {i}: invalid index {idx1}"
        assert 0 <= idx2 < len(points), f"Triangle {i}: invalid index {idx2}"


def test_decode_triangles_with_invalid_index(triangles_with_invalid_index):
    """Test du décodage de Triangles avec un indice hors bornes.

    Pourquoi : les indices doivent être validés pour éviter les accès
    out-of-bounds lors de l'utilisation des triangles.
    """
    with pytest.raises(ValueError, match="index|out of range|invalid"):
        decode_triangles(triangles_with_invalid_index)


def test_decode_triangles_truncated(triangles_truncated):
    """Test du décodage de Triangles tronqués.

    Pourquoi : les données incomplètes doivent être rejetées.
    """
    with pytest.raises(ValueError, match="truncated|incomplete"):
        decode_triangles(triangles_truncated)


def test_decode_triangles_no_triangles(triangle_points):
    """Test du décodage d'une structure Triangles sans triangles (seulement points).

    Pourquoi : cas limite valide où seuls les points sont présents.
    """
    # Encoder uniquement les points, puis count=0 pour les triangles
    buffer = struct.pack('<I', len(triangle_points))
    for x, y in triangle_points:
        buffer += struct.pack('<ff', x, y)
    buffer += struct.pack('<I', 0)  # 0 triangles

    points, triangles = decode_triangles(buffer)

    assert len(points) == len(triangle_points)
    assert len(triangles) == 0, "Should decode 0 triangles"


# Tests : Encodage Triangles

def test_encode_valid_triangles(square_points):
    """Test de l'encodage de Triangles valides.

    Pourquoi : vérifier que la structure binaire complète est correctement générée.
    """
    triangles = [(0, 1, 2), (0, 2, 3)]
    buffer = encode_triangles(square_points, triangles)

    # Vérifier la taille : PointSet + 4 bytes (count triangles) + 2*12 bytes
    expected_size = 4 + len(square_points) * 8 + 4 + len(triangles) * 12
    assert len(buffer) == expected_size, \
        f"Expected size {expected_size}, got {len(buffer)}"

    # Décoder pour vérifier
    decoded_points, decoded_triangles = decode_triangles(buffer)

    assert len(decoded_points) == len(square_points)
    assert len(decoded_triangles) == len(triangles)

    for (i_exp, j_exp, k_exp), (i_act, j_act, k_act) in zip(
        triangles, decoded_triangles
    ):
        assert i_act == i_exp
        assert j_act == j_exp
        assert k_act == k_exp


def test_encode_triangles_no_triangles(triangle_points):
    """Test de l'encodage avec 0 triangle.

    Pourquoi : cas limite où seuls les points sont encodés.
    """
    triangles = []
    buffer = encode_triangles(triangle_points, triangles)

    # Vérifier la structure
    points, decoded_triangles = decode_triangles(buffer)

    assert len(points) == len(triangle_points)
    assert len(decoded_triangles) == 0


def test_encode_triangles_single_triangle(triangle_points):
    """Test de l'encodage d'un seul triangle.

    Pourquoi : cas simple avec 1 triangle.
    """
    triangles = [(0, 1, 2)]
    buffer = encode_triangles(triangle_points, triangles)

    points, decoded_triangles = decode_triangles(buffer)

    assert len(decoded_triangles) == 1
    assert decoded_triangles[0] == (0, 1, 2)


def test_encode_triangles_pentagon(pentagon_points):
    """Test de l'encodage de triangles pour un pentagone.

    Pourquoi : cas plus complexe avec plusieurs triangles.
    """
    # Un pentagone peut être triangulé en 3 triangles
    # (cette triangulation est arbitraire, l'algo peut en générer une différente)
    triangles = [(0, 1, 2), (0, 2, 3), (0, 3, 4)]
    buffer = encode_triangles(pentagon_points, triangles)

    points, decoded_triangles = decode_triangles(buffer)

    assert len(points) == 5
    assert len(decoded_triangles) == 3


# Tests : Round-trip Triangles (encode -> decode -> égalité)
# ===========================================================================

def test_roundtrip_triangles_square(square_points):
    """Test round-trip Triangles : encode -> decode -> égalité (carré).

    Pourquoi : vérifier la cohérence complète de l'encodage/décodage Triangles.
    """
    triangles_in = [(0, 1, 2), (0, 2, 3)]
    buffer = encode_triangles(square_points, triangles_in)
    points_out, triangles_out = decode_triangles(buffer)

    # Vérifier les points
    assert len(points_out) == len(square_points)
    for (x_exp, y_exp), (x_act, y_act) in zip(square_points, points_out):
        assert x_act == pytest.approx(x_exp)
        assert y_act == pytest.approx(y_exp)

    # Vérifier les triangles
    assert len(triangles_out) == len(triangles_in)
    for tri_exp, tri_act in zip(triangles_in, triangles_out):
        assert tri_act == tri_exp


def test_roundtrip_triangles_grid(grid_points):
    """Test round-trip Triangles : encode -> decode -> égalité (grille).

    Pourquoi : vérifier avec un ensemble plus grand de points et triangles.
    """
    # Triangulation arbitraire d'une grille 3x3 (exemple simplifié)
    triangles_in = [(0, 1, 3), (1, 4, 3), (1, 2, 4), (4, 5, 2)]
    buffer = encode_triangles(grid_points, triangles_in)
    points_out, triangles_out = decode_triangles(buffer)

    assert len(points_out) == len(grid_points)
    assert len(triangles_out) == len(triangles_in)

    for tri_exp, tri_act in zip(triangles_in, triangles_out):
        assert tri_act == tri_exp


# Tests : Validation des indices (edge cases)

def test_encode_triangles_with_invalid_index_should_fail(triangle_points):
    """Test de l'encodage avec un indice triangle invalide.

    Pourquoi : l'encodage doit valider les indices avant d'écrire le buffer.
    """
    triangles = [(0, 1, 5)]  # indice 5 invalide (seulement 3 points)

    with pytest.raises(ValueError, match="index|out of range"):
        encode_triangles(triangle_points, triangles)


def test_encode_triangles_with_negative_index_should_fail(triangle_points):
    """Test de l'encodage avec un indice négatif.

    Pourquoi : les indices négatifs ne sont pas valides.
    """
    triangles = [(0, -1, 2)]

    with pytest.raises(ValueError, match="index|negative|invalid"):
        encode_triangles(triangle_points, triangles)



# Tests : Endianness explicite

def test_pointset_uses_little_endian(triangle_points):
    """Test que l'encodage PointSet utilise bien little-endian.

    Pourquoi : le format binaire est spécifié comme little-endian,
    vérifier explicitement l'ordre des bytes.
    """
    buffer = encode_pointset(triangle_points)

    # Vérifier manuellement le count avec little-endian
    count_le = struct.unpack('<I', buffer[:4])[0]
    count_be = struct.unpack('>I', buffer[:4])[0]

    assert count_le == len(triangle_points), \
        "Little-endian count should match number of points"
    assert count_be != len(triangle_points), \
        "Big-endian interpretation should differ (confirming LE usage)"


def test_triangles_uses_little_endian(square_points):
    """Test que l'encodage Triangles utilise bien little-endian.

    Pourquoi : vérification explicite de l'endianness pour Triangles.
    """
    triangles = [(0, 1, 2), (0, 2, 3)]
    buffer = encode_triangles(square_points, triangles)

    # Vérifier le count des triangles
    offset = 4 + len(square_points) * 8  # après le PointSet
    count_triangles_le = struct.unpack('<I', buffer[offset:offset+4])[0]
    count_triangles_be = struct.unpack('>I', buffer[offset:offset+4])[0]

    assert count_triangles_le == len(triangles)
    assert count_triangles_be != len(triangles)
