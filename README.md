# Learning Advisor — рекомендательная система индивидуальной траектории обучения

> Дипломный проект, МГТУ им. Баумана, кафедра ИУ5, группа ИУ5-73б

Система подбирает курсы цифровой кафедры, трек Технопарка, фокусы в дисциплинах и темы курсовых под карьерную цель студента. Студент общается с ИИ-ассистентом, а за решениями стоит экспертная система из 52 правил.

## Как это работает

```
Студент: «Хочу в ML, сейчас 5 семестр, что взять?»
                        |
                   LLM-оркестратор
                  /               \
     Экспертная система         RAG-поиск
     52 правила «если-то»      по базе знаний
                  \               /
            Персональные рекомендации:
            - Курс ЦК «Инженер ML»
            - ML-трек Технопарка
            - Упор на нейросети в лабах
            - Тема курсовой по CV
```

**LLM — переводчик, не мозг.** Все решения принимает экспертная система. LLM только понимает вопрос, вызывает нужные компоненты и формирует ответ на русском.

## Архитектура

| Компонент | Что делает | Стек |
|-----------|-----------|------|
| **Экспертная система** | 52 правила в JSON, DB-driven, CRUD через API | Python, JSON-интерпретатор |
| **RAG** | Гибридный поиск dense + BM25 -> RRF | Qdrant, text-embedding-3-small |
| **LLM-оркестратор** | Function calling: ЭС + RAG | OpenRouter API |
| **Backend** | REST API, 50 эндпоинтов, JWT-auth | FastAPI, SQLAlchemy, PostgreSQL |
| **Frontend** | SPA (в разработке) | React, TypeScript, Tailwind |

## Профиль студента

Студент заполняет минимум — система вычисляет остальное:

| Вводит студент | Система вычисляет |
|---------------|-------------------|
| Карьерная цель (11 вариантов) | Какие ЦК пройдены по категориям |
| Семестр (1-8) | Слабые стороны (средняя оценка < 4.0) |
| Статус Технопарка | Покрытие целевого профиля компетенций |
| Оценки по дисциплинам | Концентрация ЦК в категориях |
| Пройденные курсы ЦК | |

## Учебный план

В системе размечен реальный учебный план ИУ5 (направление 09.03.01, год начала 2021):
- **64 дисциплины** по 8 семестрам с формами контроля и е.з.
- **38 компетенций** привязаны к дисциплинам и курсам ЦК
- **10 карьерных направлений** с целевыми профилями компетенций
- **20 программ цифровой кафедры** с пререквизитами

## Backend API

50 эндпоинтов, 166 тестов. [Полный API-справочник](docs/API_REFERENCE.md).

```
POST /auth/register, /login, /refresh, /logout
 GET /users/me, PATCH /users/me
 GET /users/me/grades, PUT /users/me/grades
 GET /users/me/completed-ck, POST, DELETE
 GET /users/me/workload
 GET /catalog/disciplines?semester_max=N
 GET /catalog/ck-courses
 GET /expert/my-recommendations
POST /chat/message
POST /rag/search
     /admin/* — CRUD для всех сущностей
```

## Быстрый старт

```bash
# Клонирование
git clone git@github.com:sdagmir/bmstu-iu5-learning-advisor.git
cd bmstu-iu5-learning-advisor

# Backend
cp backend/.env.example backend/.env  # заполнить JWT_SECRET_KEY, LLM_API_KEY
docker-compose up -d                   # поднять приложение
docker exec -it app python -m app.admin.seed  # загрузить данные
```

## Структура проекта

```
backend/
  app/
    auth/          — JWT + bcrypt, refresh rotation
    users/         — профиль, оценки, ЦК, нагрузка, ProfileBuilder
    catalog/       — публичный каталог дисциплин и ЦК
    expert/        — 52 правила ЭС, JSON-движок
    llm/           — OpenRouter, function calling, чат
    rag/           — гибридный поиск dense+BM25, Qdrant
    admin/         — CRUD всех сущностей, seed из JSON
      seed_data/   — competencies, disciplines, ck_courses, career_directions
    db/            — SQLAlchemy модели, миграции
  tests/           — 166 юнит-тестов
docs/
  API_REFERENCE.md — полный справочник для фронтенда
```

## Стек

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x async, PostgreSQL, Qdrant, OpenRouter

**Frontend:** React, Vite, TypeScript, Tailwind CSS (в разработке)

**Инфра:** Docker, docker-compose, Alembic

---

Абитов М.Р., научный руководитель Силантьева Е.Ю., МГТУ им. Баумана, 2025
