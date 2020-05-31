run:
	docker-compose run --rm app python main.py

flush:
	docker-compose down -v --rmi all

build:
	docker-compose build

init:
	cp .env.example .env