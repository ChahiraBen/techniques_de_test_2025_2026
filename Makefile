# Makefile pour le projet Triangulator
# Techniques de Test - TP 2025/2026

.PHONY: help test unit_test perf_test coverage lint doc clean

# Commande par défaut : afficher l'aide
help:
	@echo "Commandes disponibles :"
	@echo "  make test       - Lance tous les tests (unitaires + performance)"
	@echo "  make unit_test  - Lance les tests unitaires uniquement (sans perf)"
	@echo "  make perf_test  - Lance uniquement les tests de performance"
	@echo "  make coverage   - Génère un rapport de couverture de code"
	@echo "  make lint       - Valide la qualité du code avec ruff"
	@echo "  make doc        - Génère la documentation HTML avec pdoc3"
	@echo "  make clean      - Nettoie les fichiers générés"

# Lance tous les tests (unitaires + performance)
test:
	pytest -v

# Lance uniquement les tests unitaires (exclut les tests de performance)
unit_test:
	pytest -v -m "not perf"

# Lance uniquement les tests de performance
perf_test:
	pytest -v -m perf

# Génère un rapport de couverture de code
# Note : exclut les tests de performance pour ne pas fausser les mesures
coverage:
	coverage run -m pytest -m "not perf"
	coverage report
	coverage html
	@echo "Rapport de couverture généré dans htmlcov/index.html"

# Valide la qualité du code avec ruff
lint:
	ruff check .

# Génère la documentation HTML avec pdoc3
doc:
	pdoc --html triangulator -o docs --force
	@echo "Documentation générée dans docs/triangulator/index.html"

# Nettoie les fichiers générés
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov docs
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Fichiers générés supprimés"
