"""Module de l'algorithme de triangulation.

Ce module contient l'implémentation de l'algorithme de triangulation
d'un ensemble de points 2D.
"""

from typing import List, Tuple


def triangulate(points: List[Tuple[float, float]]) -> List[Tuple[int, int, int]]:
    """Calcule la triangulation d'un ensemble de points 2D.

    Args:
        points: Liste de tuples (x, y) représentant les points à trianguler

    Returns:
        Liste de tuples (i, j, k) représentant les triangles.
        Chaque tuple contient 3 indices pointant vers les sommets dans 'points'.
        Retourne une liste vide si :
        - Moins de 3 points
        - Points colinéaires
        - Points dupliqués rendant la triangulation impossible

    Raises:
        ValueError: Si les points contiennent des NaN ou Inf
    """
    raise NotImplementedError("triangulate pas encore implémenté")
