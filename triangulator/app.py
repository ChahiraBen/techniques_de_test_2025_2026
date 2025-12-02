"""Module de l'application Flask.

Ce module contient l'API HTTP du Triangulator, exposant l'endpoint
de triangulation selon la spécification triangulator.yml.

NOTE : Cette version est un MOCK INTELLIGENT pour valider les tests API.
Elle implémente correctement tous les codes HTTP et la communication
avec le PointSetManager.
"""

import os
import re
import requests
from flask import Flask, jsonify, make_response
from triangulator.core import triangulate
from triangulator.binary import decode_pointset, encode_triangles


def create_app():
    """Factory pour créer l'application Flask.

    Returns:
        Instance de l'application Flask configurée

    Note:
        L'application expose l'endpoint GET /triangulation/{pointSetId}
        selon la spécification OpenAPI dans triangulator.yml.
    """
    app = Flask(__name__)

    # Configuration : URL du PointSetManager (via variable d'environnement ou défaut)
    POINTSET_MANAGER_URL = os.environ.get(
        'POINTSET_MANAGER_URL',
        app.config.get('POINTSET_MANAGER_URL', 'http://localhost:5000')
    )

    # Regex pour valider les UUIDs (format standard)
    UUID_REGEX = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

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
        # Validation du format UUID
        if not UUID_REGEX.match(point_set_id):
            return jsonify({
                'code': 'INVALID_UUID',
                'message': f'Invalid UUID format: {point_set_id}'
            }), 400

        # Construire l'URL de récupération du PointSet
        pointset_url = f'{POINTSET_MANAGER_URL}/pointset/{point_set_id}'

        try:
            # Récupérer le PointSet depuis le PointSetManager
            response = requests.get(pointset_url, timeout=10)

            # Gérer les différents codes de statut du PointSetManager
            if response.status_code == 404:
                # PointSet introuvable
                return jsonify({
                    'code': 'POINTSET_NOT_FOUND',
                    'message': f'PointSet with ID {point_set_id} not found'
                }), 404

            elif response.status_code == 503:
                # PointSetManager indisponible (base de données down)
                return jsonify({
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'PointSetManager service is unavailable'
                }), 503

            elif response.status_code != 200:
                # Autre erreur du PointSetManager
                return jsonify({
                    'code': 'UPSTREAM_ERROR',
                    'message': f'PointSetManager returned status {response.status_code}'
                }), 503

            # Vérifier le Content-Type (devrait être application/octet-stream)
            # Note : on accepte aussi si absent pour plus de tolérance
            content_type = response.headers.get('Content-Type', '')
            # if 'octet-stream' not in content_type and content_type:
            #     # On accepte quand même, mais pourrait être plus strict

            # Récupérer le buffer binaire
            pointset_buffer = response.content

            # Décoder le PointSet
            try:
                points = decode_pointset(pointset_buffer)
            except ValueError as e:
                # Buffer invalide ou malformé
                return jsonify({
                    'code': 'INVALID_POINTSET_DATA',
                    'message': f'Failed to decode PointSet: {str(e)}'
                }), 500

            # Effectuer la triangulation
            try:
                triangles = triangulate(points)
            except ValueError as e:
                # Erreur dans l'algorithme (NaN, Inf, etc.)
                return jsonify({
                    'code': 'TRIANGULATION_FAILED',
                    'message': f'Triangulation failed: {str(e)}'
                }), 500
            except Exception as e:
                # Autre erreur interne
                return jsonify({
                    'code': 'INTERNAL_ERROR',
                    'message': f'Internal error during triangulation: {str(e)}'
                }), 500

            # Encoder le résultat en format Triangles
            try:
                triangles_buffer = encode_triangles(points, triangles)
            except ValueError as e:
                return jsonify({
                    'code': 'ENCODING_FAILED',
                    'message': f'Failed to encode triangles: {str(e)}'
                }), 500

            # Retourner le buffer binaire avec le bon Content-Type
            response = make_response(triangles_buffer)
            response.headers['Content-Type'] = 'application/octet-stream'
            response.headers['Content-Length'] = str(len(triangles_buffer))
            return response

        except requests.exceptions.Timeout:
            # Timeout lors de la communication avec PointSetManager
            return jsonify({
                'code': 'GATEWAY_TIMEOUT',
                'message': 'Timeout while communicating with PointSetManager'
            }), 503

        except requests.exceptions.ConnectionError:
            # Erreur de connexion au PointSetManager
            return jsonify({
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Cannot connect to PointSetManager'
            }), 503

        except Exception as e:
            # Autre erreur inattendue
            return jsonify({
                'code': 'INTERNAL_ERROR',
                'message': f'Unexpected error: {str(e)}'
            }), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint de health check (optionnel mais utile)."""
        return jsonify({'status': 'ok'}), 200

    return app


# Point d'entrée pour lancer le serveur en standalone
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
