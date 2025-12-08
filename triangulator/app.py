"""Module de l'application Flask.

Ce module contient l'API HTTP du Triangulator, exposant l'endpoint
de triangulation selon la spécification triangulator.yml.
"""

import os
import re

import requests
from flask import Flask, Response, jsonify

from triangulator.binary import decode_pointset, encode_triangles
from triangulator.core import triangulate


def create_app():
    """Créer l'application Flask.

    Returns:
        Instance de l'application Flask configurée

    Note:
        L'application expose l'endpoint GET /triangulation/{pointSetId}
        selon la spécification OpenAPI dans triangulator.yml.

    """
    app = Flask(__name__)

    # Configuration de l'URL du PointSetManager
    app.config.setdefault(
        'POINTSET_MANAGER_URL',
        os.environ.get('POINTSET_MANAGER_URL', 'http://localhost:5000')
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
        # Valider le format UUID
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(point_set_id):
            return jsonify({
                'code': 'INVALID_UUID',
                'message': f'Invalid UUID format: {point_set_id}'
            }), 400

        # Construire l'URL du PointSetManager
        psm_url = app.config['POINTSET_MANAGER_URL']
        url = f'{psm_url}/pointset/{point_set_id}'

        try:
            # Récupérer le PointSet depuis le PointSetManager
            response = requests.get(url, timeout=10)

            # Gérer les différents codes de statut
            if response.status_code == 404:
                return jsonify({
                    'code': 'NOT_FOUND',
                    'message': f'PointSet with ID {point_set_id} not found'
                }), 404

            if response.status_code == 503:
                return jsonify({
                    'code': 'SERVICE_UNAVAILABLE',
                    'message': 'PointSetManager service is unavailable'
                }), 503

            if response.status_code != 200:
                return jsonify({
                    'code': 'POINTSET_MANAGER_ERROR',
                    'message': f'PointSetManager returned status {response.status_code}'
                }), 503

            # Décoder le PointSet
            try:
                pointset_buffer = response.content
                points = decode_pointset(pointset_buffer)
            except ValueError as e:
                return jsonify({
                    'code': 'INVALID_POINTSET_DATA',
                    'message': f'Failed to decode PointSet: {e!s}'
                }), 500

            # Trianguler
            try:
                triangles = triangulate(points)
            except ValueError as e:
                return jsonify({
                    'code': 'TRIANGULATION_FAILED',
                    'message': f'Triangulation error: {e!s}'
                }), 500
            except RuntimeError as e:
                return jsonify({
                    'code': 'TRIANGULATION_FAILED',
                    'message': f'Triangulation algorithm failed: {e!s}'
                }), 500

            # Encoder les Triangles
            try:
                triangles_buffer = encode_triangles(points, triangles)
            except ValueError as e:
                return jsonify({
                    'code': 'ENCODING_FAILED',
                    'message': f'Failed to encode Triangles: {e!s}'
                }), 500

            # Retourner le résultat binaire
            return Response(triangles_buffer, mimetype='application/octet-stream')

        except requests.exceptions.Timeout:
            return jsonify({
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'PointSetManager request timed out'
            }), 503

        except requests.exceptions.ConnectionError:
            return jsonify({
                'code': 'SERVICE_UNAVAILABLE',
                'message': 'Failed to connect to PointSetManager'
            }), 503

        except requests.exceptions.RequestException as e:
            return jsonify({
                'code': 'SERVICE_UNAVAILABLE',
                'message': f'PointSetManager communication error: {e!s}'
            }), 503

        except Exception as e:
            return jsonify({
                'code': 'INTERNAL_ERROR',
                'message': f'Unexpected error: {e!s}'
            }), 500

    return app
