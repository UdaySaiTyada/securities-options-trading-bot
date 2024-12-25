.PHONY: build run test clean logs monitor stop restart

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER = docker

# Commands
build:
	$(DOCKER_COMPOSE) build

run:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down

restart: stop run

logs:
	$(DOCKER_COMPOSE) logs -f

monitor:
	$(DOCKER_COMPOSE) logs -f monitoring

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".cache" -exec rm -r {} +

install:
	pip install -r requirements.txt

lint:
	flake8 .
	black .
	isort .

setup: clean install

# Development commands
dev-build:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml build

dev-run:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up -d

dev-stop:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml down
