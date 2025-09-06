# File Storage API

REST API сервис для управления файлами с автоматическим извлечением метаданных, системой ролей и уровней доступа.

## Быстрый запуск

```bash
git clone https://github.com/Alisher09072001/file-storage-api.git
cd file-storage-api
cp .env.example .env
docker compose up --build
```

API будет доступен:
- Swagger документация: http://localhost:8000/docs
- ReDoc документация: http://localhost:8000/redoc
- API: http://localhost:8000/api/v1

## Архитектура

Проект использует Clean Architecture с Unit of Work паттерном:

- **Domain** - бизнес-логика и доменные модели
- **Infrastructure** - база данных, API, внешние сервисы  
- **Service** - бизнес-сервисы использующие UoW
- **Shared** - общие компоненты (БД, JWT, MinIO)

## Система доступа

### Роли пользователей:
- **USER**: PDF файлы до 10MB, только приватные файлы
- **MANAGER**: Все типы файлов до 50MB, любая видимость, доступ ко всем отделам
- **ADMIN**: Все типы файлов до 100MB, полный доступ

### Уровни видимости:
- **PRIVATE**: Только владелец и админы
- **DEPARTMENT**: Сотрудники отдела, менеджеры и админы  
- **PUBLIC**: Все пользователи системы

### Поддерживаемые типы файлов:
- PDF документы
- Microsoft Word (DOC, DOCX)

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Вход в систему
- `GET /api/v1/auth/me` - Информация о текущем пользователе

### Users  
- `POST /api/v1/users` - Создание пользователя (менеджеры/админы)
- `GET /api/v1/users` - Список пользователей
- `GET /api/v1/users/{id}` - Информация о пользователе
- `PUT /api/v1/users/{id}/role` - Изменение роли (только админы)

### Files
- `POST /api/v1/files/upload` - Загрузка файла
- `GET /api/v1/files` - Список доступных файлов
- `GET /api/v1/files/{id}` - Информация о файле
- `GET /api/v1/files/{id}/download` - Скачивание файла
- `DELETE /api/v1/files/{id}` - Удаление файла


## Технологии

- **FastAPI** - асинхронный веб-фреймворк
- **SQLAlchemy** - асинхронный ORM
- **PostgreSQL** - основная база данных
- **Redis** - брокер сообщений для Celery
- **Celery** - асинхронная обработка задач
- **MinIO** - S3-совместимое файловое хранилище
- **Alembic** - миграции БД
- **JWT** - аутентификация
- **Docker** - контейнеризация

## Docker Services

- **app** - FastAPI приложение (порт 8000)
- **celery** - Worker для обработки метаданных
- **db** - PostgreSQL база данных (порт 5432)
- **redis** - Redis брокер (порт 6379)
- **minio** - MinIO хранилище (порт 9000, консоль 9001)

## Первый запуск

После запуска создайте миграции и первого пользователя:

```bash
# Создать миграции
docker exec -it file-storage-api-app-1 alembic revision --autogenerate -m "Initial tables"
docker exec -it file-storage-api-app-1 alembic upgrade head

# Создать админа
docker exec -it file-storage-api-app-1 python3 -c "
from shared.auth.password import password_handler
from apps.file_storage.infra.db.models import UserModel
from shared.database.connection import AsyncSessionLocal
from apps.file_storage.domain.enums.user_role import UserRole
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as session:
        hashed = password_handler.hash_password('admin123')
        user = UserModel(
            username='admin',
            hashed_password=hashed,
            role=UserRole.ADMIN,
            department='IT'
        )
        session.add(user)
        await session.commit()
        print('Admin created: username=admin, password=admin123')

asyncio.run(create_admin())
"
```

## Тестирование API

1. Перейти на http://localhost:8000/docs
2. Войти через `/auth/login` (admin / admin123)
3. Скопировать токен и использовать в заголовке: `Authorization: Bearer <token>`
4. Загрузить файл через `/files/upload`
5. Проверить извлечение метаданных

## Переменные окружения

Создайте `.env` файл из `.env.example` и настройте:

```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/filestore
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
JWT_SECRET=your-secret-key
```

## Особенности реализации

- Clean Architecture с разделением слоев
- Unit of Work паттерн для управления транзакциями
- Dependency Injection через FastAPI
- Асинхронная обработка метаданных через Celery
- Автоматические миграции БД
- Конфигурация через переменные окружения
- Swagger документация
- Docker контейнеризация

## Структура проекта

```
project/
├── shared/                 # Общие компоненты
│   ├── database/          # Подключение к БД, UoW
│   ├── storage/           # MinIO, Redis клиенты
│   └── auth/              # JWT, пароли
├── apps/file_storage/     # Модуль файлового хранилища
│   ├── domain/            # Доменные модели и логика
│   ├── infra/             # API, БД, репозитории
│   ├── service/           # Бизнес-сервисы
│   └── worker/            # Celery задачи
├── config/                # Конфигурация
├── migrations/            # Alembic миграции
└── main.py               # Точка входа
```
