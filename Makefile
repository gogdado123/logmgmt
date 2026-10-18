COMPOSE = docker compose -f docker-compose.prod.yml

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

seed:
	python samples/seed_now.py

test:
	python -m pytest tests -v