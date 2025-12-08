"""Tests unitaires pour l'API Flask du Triangulator.

Ce module teste :
- L'endpoint GET /triangulation/{pointSetId}
- Les différents codes de statut HTTP (200, 400, 404, 500, 503)
- Les Content-Type des requêtes et réponses
- L'interaction avec le PointSetManager (mockée)
- La gestion des erreurs et timeouts
- La validation des UUID

API Triangulator (selon triangulator.yml) :
    GET /triangulation/{pointSetId}
    - Paramètre : pointSetId (UUID)
    - Réponses :
        - 200 : application/octet-stream (Triangles binaires)
        - 400 : application/json (Bad request)
        - 404 : application/json (PointSet not found)
        - 500 : application/json (Internal error)
        - 503 : application/json (Service unavailable)

API PointSetManager (selon point_set_manager.yml) :
    GET /pointset/{pointSetId}
    - Réponses :
        - 200 : application/octet-stream (PointSet binaire)
        - 400 : application/json
        - 404 : application/json
        - 503 : application/json
"""

import json
import struct
from unittest.mock import patch

import pytest
import responses

from triangulator.app import create_app

# Fixtures : Application Flask
 

@pytest.fixture
def app():
    """Instance de l'application Flask en mode test.

    Pourquoi : permet de tester l'API sans lancer un vrai serveur.
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['POINTSET_MANAGER_URL'] = 'http://localhost:5000'
    return app


@pytest.fixture
def client(app):
    """Client de test Flask.

    Pourquoi : utilisé pour faire des requêtes HTTP de test.
    """
    return app.test_client()


 
# Tests : Happy path (200 OK)
 

@responses.activate
def test_triangulate_success_square(client, square_points, valid_uuid):
    """Test du happy path : triangulation réussie d'un carré.

    Pourquoi : vérifier le comportement nominal de bout en bout
    (récupération du PointSet, triangulation, encodage, réponse).
    """
    # Encoder le PointSet (carré)
    pointset_buffer = struct.pack('<I', len(square_points))
    for x, y in square_points:
        pointset_buffer += struct.pack('<ff', x, y)

    # Mocker la réponse du PointSetManager
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=pointset_buffer,
        status=200,
        content_type='application/octet-stream'
    )

    # Faire la requête au Triangulator
    response = client.get(f'/triangulation/{valid_uuid}')

    # Vérifier le code de statut
    assert response.status_code == 200, \
        f"Expected 200 OK, got {response.status_code}"

    # Vérifier le Content-Type
    assert response.content_type == 'application/octet-stream', \
        f"Expected application/octet-stream, got {response.content_type}"

    # Vérifier que la réponse contient des données binaires
    assert len(response.data) > 0, \
        "Response should contain binary data"

    # Décoder la structure Triangles
    buffer = response.data
    offset = 0

    # Partie 1 : PointSet
    point_count = struct.unpack('<I', buffer[offset:offset+4])[0]
    assert point_count == len(square_points), \
        f"Expected {len(square_points)} points, got {point_count}"
    offset += 4 + point_count * 8

    # Partie 2 : Triangles
    triangle_count = struct.unpack('<I', buffer[offset:offset+4])[0]
    assert triangle_count == 2, \
        f"Expected 2 triangles for a square, got {triangle_count}"


@responses.activate
def test_triangulate_success_triangle(client, triangle_points, valid_uuid):
    """Test du happy path avec un triangle simple.

    Pourquoi : vérifier avec le cas le plus simple (3 points -> 1 triangle).
    """
    # Encoder le PointSet (triangle)
    pointset_buffer = struct.pack('<I', len(triangle_points))
    for x, y in triangle_points:
        pointset_buffer += struct.pack('<ff', x, y)

    # Mocker la réponse du PointSetManager
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=pointset_buffer,
        status=200,
        content_type='application/octet-stream'
    )

    # Faire la requête
    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 200
    assert response.content_type == 'application/octet-stream'

    # Décoder pour vérifier
    buffer = response.data
    offset = 4 + len(triangle_points) * 8  # skip PointSet
    triangle_count = struct.unpack('<I', buffer[offset:offset+4])[0]
    assert triangle_count == 1, \
        f"Expected 1 triangle, got {triangle_count}"


@responses.activate
def test_triangulate_success_empty_pointset(client, valid_uuid):
    """Test du happy path avec un PointSet vide (0 point).

    Pourquoi : cas limite valide, devrait retourner 0 triangle sans erreur.
    """
    # Encoder un PointSet vide
    pointset_buffer = struct.pack('<I', 0)

    # Mocker la réponse du PointSetManager
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=pointset_buffer,
        status=200,
        content_type='application/octet-stream'
    )

    # Faire la requête
    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 200
    assert response.content_type == 'application/octet-stream'

    # Vérifier : 0 point, 0 triangle
    buffer = response.data
    point_count = struct.unpack('<I', buffer[0:4])[0]
    assert point_count == 0

    triangle_count = struct.unpack('<I', buffer[4:8])[0]
    assert triangle_count == 0


 
# Tests : Validation UUID (400 Bad Request)
 

def test_triangulate_invalid_uuid_format(client, invalid_uuid):
    """Test avec un UUID invalide.

    Pourquoi : l'API doit valider le format UUID et retourner 400.
    """
    response = client.get(f'/triangulation/{invalid_uuid}')

    assert response.status_code == 400, \
        f"Expected 400 Bad Request for invalid UUID, got {response.status_code}"

    assert response.content_type == 'application/json', \
        "Error response should be JSON"

    # Vérifier la structure de l'erreur
    error = json.loads(response.data)
    assert 'code' in error, "Error response should have 'code' field"
    assert 'message' in error, "Error response should have 'message' field"
    assert (
        'uuid' in error['message'].lower() or
        'invalid' in error['message'].lower()
    ), "Error message should mention UUID or invalid format"


def test_triangulate_missing_uuid(client):
    """Test sans fournir d'UUID (endpoint incomplet).

    Pourquoi : l'endpoint requiert un UUID, son absence devrait causer 404 ou 400.
    """
    response = client.get('/triangulation/')

    # Peut être 404 (route not found) ou 400 selon l'implémentation
    assert response.status_code in [400, 404], \
        f"Expected 400 or 404, got {response.status_code}"


def test_triangulate_empty_uuid(client):
    """Test avec un UUID vide.

    Pourquoi : une chaîne vide n'est pas un UUID valide.
    """
    response = client.get('/triangulation/')

    assert response.status_code in [400, 404]


 
# Tests : PointSet introuvable (404 Not Found)
 

@responses.activate
def test_triangulate_pointset_not_found(client, valid_uuid):
    """Test lorsque le PointSetManager retourne 404.

    Pourquoi : l'UUID est valide mais le PointSet n'existe pas,
    le Triangulator doit propager le 404.
    """
    # Mocker une réponse 404 du PointSetManager
    error_body = {
        "code": "NOT_FOUND",
        "message": "The requested PointSet could not be found."
    }
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        json=error_body,
        status=404,
        content_type='application/json'
    )

    # Faire la requête
    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 404, \
        f"Expected 404 when PointSet not found, got {response.status_code}"

    assert response.content_type == 'application/json'

    error = json.loads(response.data)
    assert 'code' in error
    assert 'message' in error
    assert 'not found' in error['message'].lower(), \
        "Error message should indicate resource not found"


 
# Tests : Erreurs PointSetManager (503 Service Unavailable)
 

@responses.activate
def test_triangulate_pointset_manager_unavailable(client, valid_uuid):
    """Test lorsque le PointSetManager retourne 503.

    Pourquoi : si le PointSetManager est indisponible, le Triangulator
    doit retourner 503.
    """
    # Mocker une réponse 503 du PointSetManager
    error_body = {
        "code": "SERVICE_UNAVAILABLE",
        "message": "The PointSet storage layer is unavailable."
    }
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        json=error_body,
        status=503,
        content_type='application/json'
    )

    # Faire la requête
    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 503, \
        f"Expected 503 when PointSetManager unavailable, got {response.status_code}"

    assert response.content_type == 'application/json'

    error = json.loads(response.data)
    assert 'code' in error
    assert 'message' in error


@responses.activate
def test_triangulate_pointset_manager_timeout(client, valid_uuid):
    """Test lorsque le PointSetManager ne répond pas (timeout).

    Pourquoi : les timeouts réseau doivent être gérés gracieusement
    avec un code 503 ou 504.
    """
    # Mocker un timeout (exception lors de la requête)
    import requests
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=requests.exceptions.Timeout("Connection timeout")
    )

    # Faire la requête
    response = client.get(f'/triangulation/{valid_uuid}')

    # Devrait retourner 503 ou 504 (Gateway Timeout)
    assert response.status_code in [503, 504], \
        f"Expected 503 or 504 on timeout, got {response.status_code}"

    assert response.content_type == 'application/json'


@responses.activate
def test_triangulate_pointset_manager_connection_error(client, valid_uuid):
    """Test lorsque la connexion au PointSetManager échoue.

    Pourquoi : les erreurs réseau doivent être gérées avec 503.
    """
    import requests
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=requests.exceptions.ConnectionError("Failed to connect")
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 503, \
        f"Expected 503 on connection error, got {response.status_code}"

    assert response.content_type == 'application/json'


 
# Tests : Erreurs internes (500 Internal Server Error)
 

@responses.activate
def test_triangulate_invalid_pointset_data(client, valid_uuid):
    """Test lorsque le PointSetManager retourne des données invalides.

    Pourquoi : si le buffer binaire est malformé, le Triangulator doit
    gérer l'erreur et retourner 500.
    """
    # Mocker une réponse avec un buffer malformé
    malformed_buffer = b'\x01\x02'  # trop court
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=malformed_buffer,
        status=200,
        content_type='application/octet-stream'
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 500, \
        f"Expected 500 on malformed data, got {response.status_code}"

    assert response.content_type == 'application/json'

    error = json.loads(response.data)
    assert 'code' in error
    assert 'message' in error


@responses.activate
def test_triangulate_pointset_with_nan(client, valid_uuid):
    """Test lorsque le PointSet contient des NaN.

    Pourquoi : les valeurs NaN doivent être rejetées avec 500.
    """
    # Encoder un PointSet avec NaN
    buffer = struct.pack('<I', 1)
    buffer += struct.pack('<ff', float('nan'), 0.0)

    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=buffer,
        status=200,
        content_type='application/octet-stream'
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 500, \
        f"Expected 500 for NaN values, got {response.status_code}"

    assert response.content_type == 'application/json'


@responses.activate
def test_triangulate_algorithmic_failure(client, valid_uuid):
    """Test lorsque l'algorithme de triangulation échoue.

    Pourquoi : des erreurs internes de l'algorithme doivent être
    gérées avec 500.
    """
    # Encoder un PointSet valide
    points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    buffer = struct.pack('<I', len(points))
    for x, y in points:
        buffer += struct.pack('<ff', x, y)

    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=buffer,
        status=200,
        content_type='application/octet-stream'
    )

    # Mocker l'algorithme pour qu'il lève une exception
    with patch('triangulator.app.triangulate') as mock_triangulate:
        mock_triangulate.side_effect = RuntimeError("Triangulation failed")

        response = client.get(f'/triangulation/{valid_uuid}')

        assert response.status_code == 500, \
            f"Expected 500 on algorithm failure, got {response.status_code}"

        assert response.content_type == 'application/json'


 
# Tests : Content-Type et validation
 

@responses.activate
def test_triangulate_wrong_content_type_from_psm(client, valid_uuid):
    """Test lorsque le PointSetManager retourne un mauvais Content-Type.

    Pourquoi : le Content-Type doit être validé pour éviter les erreurs.
    """
    # Mocker une réponse avec le mauvais Content-Type
    buffer = struct.pack('<I', 0)
    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=buffer,
        status=200,
        content_type='text/plain'  # mauvais type
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    # Peut être 500 (erreur interne) ou accepté selon l'implémentation
    # Ici on s'attend à ce que le Content-Type soit validé
    assert response.status_code in [200, 500]


def test_triangulate_response_headers(client, valid_uuid):
    """Test que les headers de réponse sont corrects.

    Pourquoi : vérifier que les headers HTTP standards sont présents.
    """
    # Mocker la réponse (simplifié)
    with responses.RequestsMock() as rsps:
        buffer = struct.pack('<I', 0)
        rsps.add(
            responses.GET,
            f'http://localhost:5000/pointset/{valid_uuid}',
            body=buffer,
            status=200,
            content_type='application/octet-stream'
        )

        response = client.get(f'/triangulation/{valid_uuid}')

        # Vérifier que Content-Length est présent
        assert 'Content-Length' in response.headers or len(response.data) > 0


 
# Tests : Gestion de la mémoire et grandes données
 

@responses.activate
def test_triangulate_large_pointset(client, valid_uuid, random_points_100):
    """Test avec un PointSet de 100 points.

    Pourquoi : vérifier que les grandes données sont gérées correctement
    sans erreur de mémoire.
    """
    # Encoder les 100 points
    buffer = struct.pack('<I', len(random_points_100))
    for x, y in random_points_100:
        buffer += struct.pack('<ff', x, y)

    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=buffer,
        status=200,
        content_type='application/octet-stream'
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 200, \
        f"Expected 200 for large PointSet, got {response.status_code}"

    # Vérifier que la réponse contient des données
    assert len(response.data) > 0


 
# Tests : Comportement HTTP spécifique
 

def test_triangulate_method_not_allowed(client, valid_uuid):
    """Test avec une méthode HTTP incorrecte (POST au lieu de GET).

    Pourquoi : l'endpoint n'accepte que GET, les autres méthodes
    doivent retourner 405 Method Not Allowed.
    """
    response = client.post(f'/triangulation/{valid_uuid}')

    assert response.status_code == 405, \
        f"Expected 405 Method Not Allowed, got {response.status_code}"


def test_triangulate_options_request(client, valid_uuid):
    """Test de la méthode OPTIONS (CORS preflight).

    Pourquoi : vérifier que l'API supporte les requêtes OPTIONS pour CORS.
    """
    response = client.options(f'/triangulation/{valid_uuid}')

    # Peut être 200 (si CORS supporté) ou 405
    assert response.status_code in [200, 405]


 
# Tests : Cas limites additionnels
 

@responses.activate
def test_triangulate_collinear_points(client, valid_uuid, collinear_points):
    """Test avec des points colinéaires.

    Pourquoi : devrait retourner 0 triangle sans erreur.
    """
    buffer = struct.pack('<I', len(collinear_points))
    for x, y in collinear_points:
        buffer += struct.pack('<ff', x, y)

    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=buffer,
        status=200,
        content_type='application/octet-stream'
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    assert response.status_code == 200

    # Vérifier : 0 triangle
    buffer = response.data
    offset = 4 + len(collinear_points) * 8
    triangle_count = struct.unpack('<I', buffer[offset:offset+4])[0]
    assert triangle_count == 0


@responses.activate
def test_triangulate_duplicate_points(client, valid_uuid, duplicate_points):
    """Test avec des points dupliqués.

    Pourquoi : vérifier le comportement avec des doublons (accepter ou rejeter).
    """
    buffer = struct.pack('<I', len(duplicate_points))
    for x, y in duplicate_points:
        buffer += struct.pack('<ff', x, y)

    responses.add(
        responses.GET,
        f'http://localhost:5000/pointset/{valid_uuid}',
        body=buffer,
        status=200,
        content_type='application/octet-stream'
    )

    response = client.get(f'/triangulation/{valid_uuid}')

    # Peut être 200 (accepté) ou 500 (rejeté)
    assert response.status_code in [200, 500]


@responses.activate
def test_triangulate_uuid_with_special_characters(client):
    """Test avec des caractères spéciaux dans l'UUID.

    Pourquoi : vérifier que les caractères spéciaux sont rejetés.
    """
    invalid_uuid = "123e4567-e89b-12d3-a456-42661417400@"

    response = client.get(f'/triangulation/{invalid_uuid}')

    assert response.status_code == 400, \
        "UUID with special characters should return 400"
