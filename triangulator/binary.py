"""Module de sérialisation/désérialisation binaire.

Ce module gère l'encodage et le décodage des structures PointSet et Triangles
selon les formats binaires spécifiés dans le SUJET.md.

Format PointSet (little-endian) :
    - 4 bytes : unsigned long (nombre de points)
    - N * 8 bytes : N points, chaque point = 2 floats (X, Y)

Format Triangles (little-endian) :
    - PointSet complet
    - 4 bytes : unsigned long (nombre de triangles)
    - T * 12 bytes : T triangles, chaque triangle = 3 unsigned long (indices)
"""

from typing import List, Tuple


def decode_pointset(buffer: bytes) -> List[Tuple[float, float]]:
    """Décode un buffer binaire en liste de points.

    Args:
        buffer: Buffer binaire au format PointSet

    Returns:
        Liste de tuples (x, y) représentant les points

    Raises:
        ValueError: Si le buffer est invalide ou tronqué
    """
    raise NotImplementedError("decode_pointset pas encore implémenté")


def encode_pointset(points: List[Tuple[float, float]]) -> bytes:
    """Encode une liste de points en buffer binaire.

    Args:
        points: Liste de tuples (x, y)

    Returns:
        Buffer binaire au format PointSet

    Raises:
        ValueError: Si les points contiennent des valeurs invalides (NaN, Inf)
    """
    raise NotImplementedError("encode_pointset pas encore implémenté")


def decode_triangles(buffer: bytes) -> Tuple[List[Tuple[float, float]], List[Tuple[int, int, int]]]:
    """Décode un buffer binaire en points et triangles.

    Args:
        buffer: Buffer binaire au format Triangles

    Returns:
        Tuple de (points, triangles) où :
        - points: Liste de tuples (x, y)
        - triangles: Liste de tuples (i, j, k) d'indices de sommets

    Raises:
        ValueError: Si le buffer est invalide, tronqué ou contient des indices hors-bornes
    """
    raise NotImplementedError("decode_triangles pas encore implémenté")


def encode_triangles(
    points: List[Tuple[float, float]],
    triangles: List[Tuple[int, int, int]]
) -> bytes:
    """Encode des points et triangles en buffer binaire.

    Args:
        points: Liste de tuples (x, y)
        triangles: Liste de tuples (i, j, k) d'indices de sommets

    Returns:
        Buffer binaire au format Triangles

    Raises:
        ValueError: Si les indices sont invalides ou hors-bornes
    """
    raise NotImplementedError("encode_triangles pas encore implémenté")
