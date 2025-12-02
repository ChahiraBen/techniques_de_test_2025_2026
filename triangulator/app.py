"""Module de l'application Flask.

Ce module contient l'API HTTP du Triangulator, exposant l'endpoint
de triangulation selon la spécification triangulator.yml.
"""

from flask import Flask


def create_app():
    """Factory pour créer l'application Flask.

    Returns:
        Instance de l'application Flask configurée

    Note:
        L'application expose l'endpoint GET /triangulation/{pointSetId}
        selon la spécification OpenAPI dans triangulator.yml.
    """
    app = Flask(__name__)

    @app.route('/triangulation/<point_set_id>', methods=['GET'])
    def get_triangulation(point_set_id):
        """Endpoint de triangulation.

        Args:
            point_set_id: UUID du PointSet à trianguler

        Returns:
            200: Buffer binaire (Triangles) si succès
            400: JSON error si UUID invalide
            404: JSON error si PointSet introuvable
            500: JSON error si erreur interne
            503: JSON error si PointSetManager indisponible
        """
        raise NotImplementedError("Endpoint /triangulation pas encore implémenté")

    return app
