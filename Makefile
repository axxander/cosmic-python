export COMPOSE_DOCKER_CLI_BUILD=1	
export DOCKER_BUILDKIT=1

all: down build up test

build:
	docker-compose build

up:
	docker-compose up -d app

down:
	docker-compose down

logs: 
	docker-compose logs app | tail -100

test:
	pytest --tb=short

install-deps:
	pip install -U pip pip-tools
	pip-sync requirements.txt

update-deps:
	pip-compile requirements.in --output-file requirements.txt --upgrade
	make install-deps
