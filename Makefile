# Makefile для Product Search Tool

.PHONY: help build up down logs restart clean dev prod test

# Переменные
COMPOSE_FILE_DEV = docker-compose.yml
COMPOSE_FILE_PROD = docker-compose.prod.yml

help: ## Показать справку
	@echo "Product Search Tool - Команды для управления"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Собрать Docker образы
	@echo "🔨 Собираем Docker образы..."
	docker-compose -f $(COMPOSE_FILE_DEV) build

build-prod: ## Собрать Docker образы для продакшена
	@echo "🔨 Собираем Docker образы для продакшена..."
	docker-compose -f $(COMPOSE_FILE_PROD) build

up: ## Запустить в режиме разработки
	@echo "🚀 Запускаем в режиме разработки..."
	docker-compose -f $(COMPOSE_FILE_DEV) up -d
	@echo "✅ Сервисы запущены:"
	@echo "   Frontend: http://localhost"
	@echo "   Backend: http://localhost:5003"

prod: ## Запустить в режиме продакшена
	@echo "🏭 Запускаем в режиме продакшена..."
	docker-compose -f $(COMPOSE_FILE_PROD) up -d
	@echo "✅ Сервисы запущены в продакшене"

down: ## Остановить все сервисы
	@echo "🛑 Останавливаем сервисы..."
	docker-compose -f $(COMPOSE_FILE_DEV) down --remove-orphans
	docker-compose -f $(COMPOSE_FILE_PROD) down --remove-orphans

logs: ## Показать логи всех сервисов
	docker-compose -f $(COMPOSE_FILE_DEV) logs -f

logs-backend: ## Показать логи backend
	docker-compose -f $(COMPOSE_FILE_DEV) logs -f backend

logs-frontend: ## Показать логи frontend
	docker-compose -f $(COMPOSE_FILE_DEV) logs -f frontend

restart: ## Перезапустить сервисы
	@echo "🔄 Перезапускаем сервисы..."
	docker-compose -f $(COMPOSE_FILE_DEV) restart

restart-backend: ## Перезапустить только backend
	@echo "🔄 Перезапускаем backend..."
	docker-compose -f $(COMPOSE_FILE_DEV) restart backend

restart-frontend: ## Перезапустить только frontend
	@echo "🔄 Перезапускаем frontend..."
	docker-compose -f $(COMPOSE_FILE_DEV) restart frontend

status: ## Показать статус сервисов
	@echo "📊 Статус сервисов:"
	docker-compose -f $(COMPOSE_FILE_DEV) ps

health: ## Проверить health check
	@echo "🏥 Проверяем health check..."
	@curl -f http://localhost:5003/health && echo "✅ Backend здоров" || echo "❌ Backend не отвечает"
	@curl -f http://localhost/ > /dev/null 2>&1 && echo "✅ Frontend здоров" || echo "❌ Frontend не отвечает"

clean: ## Очистить все Docker ресурсы
	@echo "🧹 Очищаем Docker ресурсы..."
	docker-compose -f $(COMPOSE_FILE_DEV) down --remove-orphans --volumes
	docker-compose -f $(COMPOSE_FILE_PROD) down --remove-orphans --volumes
	docker system prune -f
	docker volume prune -f

shell-backend: ## Войти в контейнер backend
	docker-compose -f $(COMPOSE_FILE_DEV) exec backend /bin/bash

shell-frontend: ## Войти в контейнер frontend
	docker-compose -f $(COMPOSE_FILE_DEV) exec frontend /bin/sh

test: ## Запустить тесты
	@echo "🧪 Запускаем тесты..."
	docker-compose -f $(COMPOSE_FILE_DEV) exec backend python -m pytest tests/ -v

install: ## Первоначальная установка
	@echo "📦 Первоначальная установка..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Создан файл .env. Отредактируйте его и добавьте API ключи."; \
	fi
	$(MAKE) build
	$(MAKE) up
	@echo "🎉 Установка завершена!"

deploy: ## Полный деплой (остановка, сборка, запуск)
	@echo "🚀 Полный деплой..."
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up
	$(MAKE) health

deploy-prod: ## Полный деплой в продакшене
	@echo "🏭 Полный деплой в продакшене..."
	$(MAKE) down
	$(MAKE) build-prod
	$(MAKE) prod
	$(MAKE) health
