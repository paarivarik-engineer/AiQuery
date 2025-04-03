.PHONY: init db migrate up down test clean

init: 
	@echo "Initializing project..."
	@echo "1. Ensuring clean state..."
	@docker-compose down -v --remove-orphans --timeout 30 >/dev/null 2>&1 || true
	@echo "2. Building containers with full logs..."
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --no-cache --progress=plain
	@echo "\n3. Starting database service..."
	docker-compose up -d db
	@echo "Waiting for database to be ready (max 60 seconds)..."
	@(timeout=60; \
	while [ $$timeout -gt 0 ]; do \
		if docker-compose exec db pg_isready -U aiquery; then \
			echo "Database is ready!"; \
			break; \
		fi; \
		echo "Database starting... ($$timeout seconds remaining)"; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done; \
	if [ $$timeout -le 0 ]; then echo "Database startup timed out!"; exit 1; fi)
	@echo "\n4. Running database migrations..."
	docker-compose run web flask db upgrade
	@echo "\n5. Initialization complete!"
	@echo "Run 'make up' to start the application"

db:
	@echo "Starting database..."
	docker-compose up -d db

migrate:
	@echo "Creating new migration..."
	docker-compose run web flask db migrate -m "automatic migration"

up:
	@echo "Starting services..."
	docker-compose up

down:
	@echo "Stopping services..."
	docker-compose down

test:
	@echo "Running tests with coverage..."
	docker-compose run web pytest --cov=app --cov-report=term-missing

test-html:
	@echo "Running tests with HTML coverage report..."
	docker-compose run web pytest --cov=app --cov-report=html

test-unit:
	@echo "Running unit tests..."
	docker-compose run web pytest tests/unit/

test-integration:
	@echo "Running integration tests..."
	docker-compose run web pytest tests/integration/

test-functional:
	@echo "Running functional tests..."
	docker-compose run web pytest tests/functional/

test-db:
	@echo "Setting up test database..."
	docker-compose exec db psql -U aiquery -c "CREATE DATABASE aiquery_test;"

clean:
	@echo "1. Stopping and removing containers..."
	docker-compose down -v --remove-orphans --timeout 30
	@echo "2. Removing local files..."
	rm -rf instance/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "3. Pruning Docker system..."
	@echo "docker system prune -f"
	@echo "Cleanup complete!"

logs:
	@echo "Showing logs..."
	docker-compose logs -f

shell:
	@echo "Opening shell..."
	docker-compose run web flask shell

admin:
	@echo "Creating admin user..."
	docker-compose run web flask create-admin
