# TODO
Plan de tests:
Objectif: Ce plan de tests décrit la stratégie de validation du composant Triangulator.
L'objectif est de garantir: le bon fonctionnement de l'algorithme de triangulation, la conformité de l'API exposé, la performance du code te la qualité globale du projet
TESTS DE COMPORTEMENT:
Tests Unitaire:
1. Décoder un PointSet valide:
pourquoi:vérifier que un buffer binaire est correctement interprété
Comment:créer un buffer avec trois points connus, vérifier que la fonction renvoie la liste [(0,0),(1,0),(0,1)]
2. Décoder un PointSet tronqué:
   Pourquoi: s'assurer qu'une erreur est levée en cas de données incomplètes
   Comment:créer un buffer annonçant 3 points mais n'en contenant que 2, vérifier qu'une erreur est levé
3. Encoder puis décoder un PointSet:
   Pourquoi:tester la cohérence de l'encodage/décodage
   Comment:Encoder une liste de points, puis décoder et comparer au résultat initial
4. Décoder un triangles valide
   Pourquoi: Vérifier la lecture correcte de la partie triangles du binaire 
   Comment:créer un buffer avec 4 points et 2 triangles vérifier la cohérence des indices
5. Moins de 3 points:
   Pourquoi: aucun triangle est possible
   Comment: Fournir 0 ,1 ou 2 points vérifier que la listes des triangles est vide
6. Trois points forment un triangle:
   Pourquoi: Cas minimal valide
   Comment: Fournir [(0,0),(1,0),(0,1)] attendre 1 triangle[(0,1,2)]
7. Trois points colinéaires:
   Pourquoi: Pas de triangle valide
   Comment:Fournir [(0,0),(1,0),(2,0)] résultat vide
8. Carré de 4 points:
   Pourquoi: cas simple à 2 triangles
   Comment:Fournir 4 points[(0,0),(1,0),(1,1),(0,1)] attendre 2 triangle cohérent

Tests d'intégration/API
9. Happy path:
   Pourquoi: vérifier le fonctionnement complet (de la requête à la réponse) avec des données valides
   Comment: envoyer une requête Post avec un json le PointSetManager renvoie un pointSet binaire de 4 point formant un carré  
   Attendus: une reponse HTTP 200 ok et un buffer binaire qui contient 2 triangles cohérent
10. Entrée invalide
    Pourquoi: Vérifier que le Triangulator relie correctement une erreur pointset_ID introuvable
    Comment:mocker la réponse de PointSetManager HTTP 404 NOT FOUND
    Attendus: 404 Not Found


TEST DE COUVERTURE :
Pourquoi:garantir que tous les chemins logiques sont stockés
Comment: utiliser coverage avec pytest 
attendus: couverture> 90% sur les modules de logique


TESTS DE PERFORMANCE:
1. Trinagulation de grands ensembles de points:
   Pourquoi:évaluer la complexité et la rapidité de l'algorithme
   Comment:générer aléatoirement des pointSet de tailles croissante et mesurer le temps d'exécution
   Attendus: le temps augmente de façon proportionnelle pas d'explosion exponentielle
2. Encodage/Décodage de buffers binaires
   Pourquoi:Vérifier que la sérialisation reste efficace
   Comment:encoder et décoder plusieurs PointsSet de tailles variées en mesurant le temps moyen
   attendus: un temps raisonnable




   


