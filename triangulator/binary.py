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

NOTE : Cette implémentation est fonctionnelle (pas un mock).
La sérialisation binaire est simple et ne nécessite pas d'algorithme complexe.
"""

import struct
import math
from typing import List, Tuple


def decode_pointset(buffer: bytes) -> List[Tuple[float, float]]:
    """Décode un buffer binaire en liste de points.

    Args:
        buffer: Buffer binaire au format PointSet

    Returns:
        Liste de tuples (x, y) représentant les points

    Raises:
        ValueError: Si le buffer est invalide, tronqué, ou contient NaN/Inf
    """
    # Vérifier la taille minimale (au moins le count)
    if len(buffer) < 4:
        raise ValueError("Buffer too short: cannot read point count (truncated)")

    # Lire le nombre de points
    try:
        count = struct.unpack('<I', buffer[:4])[0]
    except struct.error as e:
        raise ValueError(f"Failed to unpack point count: {e}")

    # Vérifier que le buffer contient assez de données
    expected_size = 4 + count * 8
    if len(buffer) < expected_size:
        raise ValueError(
            f"Buffer truncated: expected {expected_size} bytes for {count} points, "
            f"got {len(buffer)} bytes (incomplete data)"
        )

    # Décoder les points
    points = []
    offset = 4
    for i in range(count):
        try:
            x, y = struct.unpack('<ff', buffer[offset:offset+8])
        except struct.error as e:
            raise ValueError(f"Failed to unpack point {i}: {e}")

        # Valider les valeurs
        if math.isnan(x) or math.isnan(y):
            raise ValueError(f"Point {i} contains NaN values (invalid)")
        if math.isinf(x) or math.isinf(y):
            raise ValueError(f"Point {i} contains Inf values (invalid)")

        points.append((x, y))
        offset += 8

    return points


def encode_pointset(points: List[Tuple[float, float]]) -> bytes:
    """Encode une liste de points en buffer binaire.

    Args:
        points: Liste de tuples (x, y)

    Returns:
        Buffer binaire au format PointSet

    Raises:
        ValueError: Si les points contiennent des valeurs invalides (NaN, Inf)
    """
    # Valider les points avant encodage
    for i, (x, y) in enumerate(points):
        if math.isnan(x) or math.isnan(y):
            raise ValueError(f"Cannot encode point {i}: contains NaN values")
        if math.isinf(x) or math.isinf(y):
            raise ValueError(f"Cannot encode point {i}: contains Inf values")

    # Encoder le count
    buffer = struct.pack('<I', len(points))

    # Encoder les points
    for x, y in points:
        buffer += struct.pack('<ff', x, y)

    return buffer


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
    # Décoder la partie PointSet
    points = decode_pointset(buffer)

    # Calculer l'offset après le PointSet
    offset = 4 + len(points) * 8

    # Vérifier qu'on peut lire le nombre de triangles
    if len(buffer) < offset + 4:
        raise ValueError("Buffer truncated: cannot read triangle count (incomplete)")

    # Lire le nombre de triangles
    try:
        triangle_count = struct.unpack('<I', buffer[offset:offset+4])[0]
    except struct.error as e:
        raise ValueError(f"Failed to unpack triangle count: {e}")

    offset += 4

    # Vérifier que le buffer contient tous les triangles
    expected_size = offset + triangle_count * 12
    if len(buffer) < expected_size:
        raise ValueError(
            f"Buffer truncated: expected {expected_size} bytes for {triangle_count} triangles, "
            f"got {len(buffer)} bytes (incomplete)"
        )

    # Décoder les triangles
    triangles = []
    for t in range(triangle_count):
        try:
            i, j, k = struct.unpack('<III', buffer[offset:offset+12])
        except struct.error as e:
            raise ValueError(f"Failed to unpack triangle {t}: {e}")

        # Valider les indices
        if i >= len(points):
            raise ValueError(f"Triangle {t}: index {i} out of range (max {len(points)-1})")
        if j >= len(points):
            raise ValueError(f"Triangle {t}: index {j} out of range (max {len(points)-1})")
        if k >= len(points):
            raise ValueError(f"Triangle {t}: index {k} out of range (max {len(points)-1})")

        triangles.append((i, j, k))
        offset += 12

    return points, triangles


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
        ValueError: Si les indices sont invalides, négatifs ou hors-bornes
    """
    # Valider les indices avant encodage
    for t, (i, j, k) in enumerate(triangles):
        if i < 0 or j < 0 or k < 0:
            raise ValueError(f"Triangle {t}: indices cannot be negative (got {i}, {j}, {k})")
        if i >= len(points):
            raise ValueError(f"Triangle {t}: index {i} out of range (max {len(points)-1})")
        if j >= len(points):
            raise ValueError(f"Triangle {t}: index {j} out of range (max {len(points)-1})")
        if k >= len(points):
            raise ValueError(f"Triangle {t}: index {k} out of range (max {len(points)-1})")

    # Encoder la partie PointSet
    buffer = encode_pointset(points)

    # Encoder le nombre de triangles
    buffer += struct.pack('<I', len(triangles))

    # Encoder les triangles
    for i, j, k in triangles:
        buffer += struct.pack('<III', i, j, k)

    return buffer
