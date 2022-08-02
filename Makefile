include .env

tail := 200
PYTHONPATH := $(shell pwd):${PYTHONPATH}

PROJECT := tiktok-viewer-public
PIPENV_VERBOSITY := -1

# =================================================================================================
# Base
# =================================================================================================

default:help

help:
	@echo "Hello. Check README.md"

# =================================================================================================
# Development
# =================================================================================================

flake8:
	flake8 app

lint: flake8

app:
	exec ${PYTHONPATH} manage.py

locust:
	echo "Locust"

# =================================================================================================
# Docker
# =================================================================================================

docker-config:
	docker-compose config

docker-ps:
	docker-compose ps

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d --remove-orphans

docker-stop:
	docker-compose stop

docker-down:
	docker-compose down

docker-destroy:
	docker-compose down -v --remove-orphans

docker-logs:
	docker-compose logs -f --tail=${tail} ${args}


# =================================================================================================
# Application in Docker
# =================================================================================================

app-create: docker-build docker-stop docker-up

app-logs:
	$(MAKE) docker-logs args="app"

app-stop: docker-stop

app-down: docker-down

app-start: docker-stop docker-up

app-destroy: docker-destroy
