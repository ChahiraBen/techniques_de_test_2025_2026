"""Configuration et fixtures partagées pour tous les tests.

Ce module contient les fixtures pytest réutilisables pour :
- Générer des données binaires valides (PointSet, Triangles)
- Créer des ensembles de points de test (triangle, carré, grille, etc.)
- Fournir des buffers binaires malformés pour tester la robustesse
- Configurer le client Flask de test
"""

import math
import random
import struct

import pytest

# FIXTURES : Données de points (géométrie pure)

@pytest.fixture
def triangle_points() -> list[tuple[float, float]]:
    """Points formant un triangle simple.

    Pourquoi : cas de base pour tester un triangle valide.
    """
    return [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]


@pytest.fixture
def collinear_points() -> list[tuple[float, float]]:
    """Points alignés sur une même ligne.

    Pourquoi : aucun triangle ne peut être formé, teste les cas dégénérés.
    """
    return [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]


@pytest.fixture
def square_points() -> list[tuple[float, float]]:
    """Points formant un carré.

    Pourquoi : devrait produire exactement 2 triangles non-chevauchants.
    """
    return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


@pytest.fixture
def pentagon_points() -> list[tuple[float, float]]:
    """Points formant un pentagone régulier.

    Pourquoi : teste un cas plus complexe avec plusieurs triangles.
    """
    points = []
    for i in range(5):
        angle = 2 * math.pi * i / 5
        x = math.cos(angle)
        y = math.sin(angle)
        points.append((x, y))
    return points


@pytest.fixture
def grid_points() -> list[tuple[float, float]]:
    """Points disposés en grille 3x3.

    Pourquoi : teste la triangulation d'une distribution régulière.
    """
    points = []
    for i in range(3):
        for j in range(3):
            points.append((float(i), float(j)))
    return points


@pytest.fixture
def random_points_10() -> list[tuple[float, float]]:
    """10 points aléatoires avec seed fixe.

    Pourquoi : teste une distribution aléatoire reproductible.
    """
    random.seed(42)
    return [(random.uniform(0, 10), random.uniform(0, 10)) for _ in range(10)]


@pytest.fixture
def random_points_100() -> list[tuple[float, float]]:
    """100 points aléatoires avec seed fixe.

    Pourquoi : pour les tests de performance ou de robustesse.
    """
    random.seed(123)
    return [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(100)]


@pytest.fixture
def duplicate_points() -> list[tuple[float, float]]:
    """Points contenant des doublons.

    Pourquoi : teste le comportement avec des points identiques.
    """
    return [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, 0.0)]


@pytest.fixture
def two_points() -> list[tuple[float, float]]:
    """Seulement 2 points.

    Pourquoi : insuffisant pour former un triangle, devrait retourner 0 triangle.
    """
    return [(0.0, 0.0), (1.0, 1.0)]


@pytest.fixture
def empty_points() -> list[tuple[float, float]]:
    """Aucun point.

    Pourquoi : cas limite, devrait retourner 0 triangle.
    """
    return []


 
# FIXTURES : Données binaires (PointSet)
 

@pytest.fixture
def valid_pointset_binary(triangle_points) -> bytes:
    """Buffer binaire valide représentant un PointSet (triangle).

    Pourquoi : pour tester le décodage d'un PointSet valide.
    Format : 4 bytes count + 8 bytes par point (4 bytes X, 4 bytes Y).
    """
    count = len(triangle_points)
    buffer = struct.pack('<I', count)  # unsigned long, little-endian
    for x, y in triangle_points:
        buffer += struct.pack('<ff', x, y)  # 2 floats
    return buffer


@pytest.fixture
def truncated_pointset_binary() -> bytes:
    """Buffer binaire PointSet tronqué (annonce 3 points mais n'en contient que 2).

    Pourquoi : teste la robustesse face à des données incomplètes.
    """
    buffer = struct.pack('<I', 3)  # annonce 3 points
    buffer += struct.pack('<ff', 0.0, 0.0)  # point 1
    buffer += struct.pack('<ff', 1.0, 0.0)  # point 2
    # manque le point 3
    return buffer


@pytest.fixture
def empty_pointset_binary() -> bytes:
    """Buffer binaire PointSet vide (0 point).

    Pourquoi : cas limite valide, devrait être décodé sans erreur.
    """
    return struct.pack('<I', 0)


@pytest.fixture
def malformed_pointset_binary() -> bytes:
    """Buffer binaire malformé (trop court pour contenir le count).

    Pourquoi : teste la gestion des erreurs de parsing.
    """
    return b'\x01\x00'  # seulement 2 bytes au lieu de 4


@pytest.fixture
def pointset_with_nan() -> bytes:
    """Buffer binaire PointSet contenant des NaN.

    Pourquoi : teste le rejet des valeurs invalides.
    """
    buffer = struct.pack('<I', 1)
    buffer += struct.pack('<ff', float('nan'), 0.0)
    return buffer


@pytest.fixture
def pointset_with_inf() -> bytes:
    """Buffer binaire PointSet contenant des Inf.

    Pourquoi : teste le rejet des valeurs infinies.
    """
    buffer = struct.pack('<I', 1)
    buffer += struct.pack('<ff', float('inf'), 0.0)
    return buffer


# FIXTURES : Données binaires (Triangles)

@pytest.fixture
def valid_triangles_binary(square_points) -> bytes:
    """Buffer binaire valide représentant des Triangles (carré -> 2 triangles).

    Pourquoi : pour tester le décodage d'une structure Triangles valide.
    Format : PointSet + 4 bytes count triangles + 12 bytes par triangle.
    """
    # Partie 1 : PointSet (4 points du carré)
    buffer = struct.pack('<I', len(square_points))
    for x, y in square_points:
        buffer += struct.pack('<ff', x, y)

    # Partie 2 : Triangles (2 triangles : [0,1,2] et [0,2,3])
    triangles = [(0, 1, 2), (0, 2, 3)]
    buffer += struct.pack('<I', len(triangles))
    for i, j, k in triangles:
        buffer += struct.pack('<III', i, j, k)

    return buffer


@pytest.fixture
def triangles_with_invalid_index() -> bytes:
    """Buffer binaire Triangles avec un indice hors bornes.

    Pourquoi : teste la validation des indices de sommets.
    """
    # 3 points
    buffer = struct.pack('<I', 3)
    buffer += struct.pack('<ff', 0.0, 0.0)
    buffer += struct.pack('<ff', 1.0, 0.0)
    buffer += struct.pack('<ff', 0.0, 1.0)

    # 1 triangle avec un indice invalide (5 >= 3)
    buffer += struct.pack('<I', 1)
    buffer += struct.pack('<III', 0, 1, 5)  # indice 5 est invalide

    return buffer


@pytest.fixture
def triangles_truncated() -> bytes:
    """Buffer binaire Triangles tronqué.

    Pourquoi : teste la robustesse face à des données incomplètes.
    """
    # 3 points
    buffer = struct.pack('<I', 3)
    buffer += struct.pack('<ff', 0.0, 0.0)
    buffer += struct.pack('<ff', 1.0, 0.0)
    buffer += struct.pack('<ff', 0.0, 1.0)

    # Annonce 2 triangles mais n'en contient qu'1
    buffer += struct.pack('<I', 2)
    buffer += struct.pack('<III', 0, 1, 2)
    # manque le 2ème triangle

    return buffer


# FIXTURES : Client Flask et mocking


@pytest.fixture
def flask_client():
    """Client Flask de test.

    Pourquoi : permet de tester l'API sans lancer un vrai serveur.
    Note : nécessite que l'app Flask soit importable depuis triangulator.app
    """
    # Cette fixture sera implémentée quand l'app existera
    # Pour l'instant, elle servira de placeholder dans les tests
    from triangulator.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_pointset_manager_url() -> str:
    """URL du PointSetManager pour les tests.

    Pourquoi : centralise l'URL mockée pour tous les tests API.
    """
    return "http://pointset-manager:5000"


@pytest.fixture
def valid_uuid() -> str:
    """UUID valide pour les tests.

    Pourquoi : utilisé dans les requêtes API de test.
    """
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def invalid_uuid() -> str:
    """UUID invalide pour les tests.

    Pourquoi : teste la validation du format UUID.
    """
    return "not-a-valid-uuid"


# FIXTURES : Helpers et utilitaires

@pytest.fixture
def binary_encoder():
    """Encode un PointSet en format binaire.

    Pourquoi : évite la duplication de code dans les tests.
    """
    def encode(points: list[tuple[float, float]]) -> bytes:
        buffer = struct.pack('<I', len(points))
        for x, y in points:
            buffer += struct.pack('<ff', x, y)
        return buffer
    return encode


@pytest.fixture
def binary_decoder():
    """Décode un PointSet depuis son format binaire.

    Pourquoi : évite la duplication de code dans les tests.
    """
    def decode(buffer: bytes) -> list[tuple[float, float]]:
        # Cette fonction sera implémentée dans le code de production
        # Pour l'instant, c'est un placeholder pour les tests
        from triangulator.binary import decode_pointset
        return decode_pointset(buffer)
    return decode


@pytest.fixture
def triangles_encoder():
    """Encode des Triangles en format binaire.

    Pourquoi : évite la duplication de code dans les tests.
    """
    def encode(
        points: list[tuple[float, float]],
        triangles: list[tuple[int, int, int]]
    ) -> bytes:
        # Partie 1 : PointSet
        buffer = struct.pack('<I', len(points))
        for x, y in points:
            buffer += struct.pack('<ff', x, y)

        # Partie 2 : Triangles
        buffer += struct.pack('<I', len(triangles))
        for i, j, k in triangles:
            buffer += struct.pack('<III', i, j, k)

        return buffer
    return encode
