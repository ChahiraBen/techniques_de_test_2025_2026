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



def decode_pointset(buffer: bytes) -> list[tuple[float, float]]:
    """Décode un buffer binaire en liste de points.

    Args:
        buffer: Buffer binaire au format PointSet

    Returns:
        Liste de tuples (x, y) représentant les points

    Raises:
        ValueError: Si le buffer est invalide ou tronqué

    """
    import math
    import struct

    # Vérifier que le buffer contient au moins le count (4 bytes)
    if len(buffer) < 4:
        raise ValueError("Buffer is too short to contain point count")

    # Extraire le nombre de points (little-endian unsigned long)
    count = struct.unpack('<I', buffer[0:4])[0]

    # Vérifier que le buffer contient bien tous les points
    expected_size = 4 + count * 8  # 4 bytes count + 8 bytes par point
    if len(buffer) < expected_size:
        msg = f"Buffer is truncated: expected {expected_size} bytes, got {len(buffer)}"
        raise ValueError(msg)

    # Décoder les points
    points = []
    offset = 4
    for _ in range(count):
        x, y = struct.unpack('<ff', buffer[offset:offset+8])

        # Valider les coordonnées (rejeter NaN et Inf)
        if math.isnan(x) or math.isnan(y):
            raise ValueError("Point contains NaN values")
        if math.isinf(x) or math.isinf(y):
            raise ValueError("Point contains infinite values")

        points.append((x, y))
        offset += 8

    return points


def encode_pointset(points: list[tuple[float, float]]) -> bytes:
    """Encode une liste de points en buffer binaire.

    Args:
        points: Liste de tuples (x, y)

    Returns:
        Buffer binaire au format PointSet

    Raises:
        ValueError: Si les points contiennent des valeurs invalides (NaN, Inf)

    """
    import math
    import struct

    # Encoder le nombre de points (little-endian unsigned long)
    buffer = struct.pack('<I', len(points))

    # Encoder chaque point
    for x, y in points:
        # Valider les coordonnées
        if math.isnan(x) or math.isnan(y):
            raise ValueError("Point contains NaN values")
        if math.isinf(x) or math.isinf(y):
            raise ValueError("Point contains infinite values")

        buffer += struct.pack('<ff', x, y)

    return buffer


def decode_triangles(
    buffer: bytes,
) -> tuple[list[tuple[float, float]], list[tuple[int, int, int]]]:
    """Décode un buffer binaire en points et triangles.

    Args:
        buffer: Buffer binaire au format Triangles

    Returns:
        Tuple de (points, triangles) où :
        - points: Liste de tuples (x, y)
        - triangles: Liste de tuples (i, j, k) d'indices de sommets

    Raises:
        ValueError: Si le buffer est invalide, tronqué ou hors-bornes.

    """
    import struct

    # Partie 1 : Décoder les points
    if len(buffer) < 4:
        raise ValueError("Buffer is too short to contain point count")

    point_count = struct.unpack('<I', buffer[0:4])[0]
    pointset_size = 4 + point_count * 8

    if len(buffer) < pointset_size:
        raise ValueError("Buffer is truncated in PointSet section")

    # Décoder le PointSet en utilisant la fonction existante
    points = decode_pointset(buffer[:pointset_size])

    # Partie 2 : Décoder les triangles
    offset = pointset_size

    if len(buffer) < offset + 4:
        raise ValueError("Buffer is too short to contain triangle count")

    triangle_count = struct.unpack('<I', buffer[offset:offset+4])[0]
    offset += 4

    expected_size = offset + triangle_count * 12  # 12 bytes par triangle
    if len(buffer) < expected_size:
        raise ValueError("Buffer is truncated or incomplete in triangles section")

    # Décoder les triangles
    triangles = []
    for _ in range(triangle_count):
        i, j, k = struct.unpack('<III', buffer[offset:offset+12])

        # Valider les indices
        if i < 0 or i >= point_count:
            raise ValueError(f"Triangle index {i} is out of range [0, {point_count})")
        if j < 0 or j >= point_count:
            raise ValueError(f"Triangle index {j} is out of range [0, {point_count})")
        if k < 0 or k >= point_count:
            raise ValueError(f"Triangle index {k} is out of range [0, {point_count})")

        triangles.append((i, j, k))
        offset += 12

    return points, triangles


def encode_triangles(
    points: list[tuple[float, float]],
    triangles: list[tuple[int, int, int]]
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
    import struct

    # Valider les indices des triangles avant l'encodage
    for triangle_idx, (i, j, k) in enumerate(triangles):
        if i < 0 or j < 0 or k < 0:
            raise ValueError(f"Triangle {triangle_idx} contains negative index")
        if i >= len(points) or j >= len(points) or k >= len(points):
            raise ValueError(f"Triangle {triangle_idx} contains index out of range")

    # Partie 1 : Encoder le PointSet
    buffer = encode_pointset(points)

    # Partie 2 : Encoder les triangles
    buffer += struct.pack('<I', len(triangles))

    for i, j, k in triangles:
        buffer += struct.pack('<III', i, j, k)

    return buffer
