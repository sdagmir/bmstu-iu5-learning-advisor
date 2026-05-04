# admin — Административный модуль

## Что делает

Полный CRUD для всех данных системы + управление пользователями.
Все эндпоинты требуют роль `admin`.

## Сущности

| Сущность | Операции | Кол-во в seed | Описание |
|----------|----------|---------------|----------|
| Users | R, U | -- | Список пользователей, смена роли/блокировка |
| Competencies | CRUD | 38 | Теги компетенций (8 категорий) |
| Disciplines | CRUD | 64 | Учебный план ИУ5 (8 семестров) |
| CK Courses | CRUD | 20 | Программы цифровой кафедры (2 е.з.) |
| Career Directions | CRUD | 10 | Направления + целевые профили компетенций |
| Focus Advices | CRUD | -- | Фокусы (дисциплина x направление -> совет) |
| Rules | CRUD | 52 | Правила ЭС в JSON |

## Seed-данные в JSON

```
seed_data/
  competencies.json       -- 38 тегов (8 категорий)
  career_directions.json  -- 10 направлений + example_jobs
  disciplines.json        -- 64 дисциплины учебного плана ИУ5
  ck_courses.json         -- 20 программ ЦК (description -> для RAG позже)
```

```bash
python -m app.admin.seed   # идемпотентный, пропускает существующие
```

Seed = начальное наполнение. Дальше все через Admin API.

## M:N связи

Дисциплины, ЦК и направления привязываются к компетенциям через `competency_ids`.
ЦК дополнительно имеют `prerequisite_ids` (пререквизиты).
При PATCH `competency_ids` **заменяет** весь список (не добавляет).

## Пагинация

Все списки: `offset` (default 0) + `limit` (default 50, max 100).
Нет total_count -- конец списка: `len(result) < limit`.

## API

| Группа | Методы | Путь |
|--------|--------|------|
| Users | GET, GET/{id}, PATCH/{id} | `/admin/users` |
| Competencies | GET, POST, PATCH/{id}, DELETE/{id} | `/admin/competencies` |
| Disciplines | GET, POST, PATCH/{id}, DELETE/{id} | `/admin/disciplines` |
| CK Courses | GET, POST, PATCH/{id}, DELETE/{id} | `/admin/ck-courses` |
| Career Directions | GET, POST, PATCH/{id}, DELETE/{id} | `/admin/career-directions` |
| Focus Advices | GET, POST, PATCH/{id}, DELETE/{id} | `/admin/focus-advices` |
| Rules | GET, POST, PATCH/{id}, DELETE/{id} | `/admin/rules` |
| LLM traces | GET, GET/{id} | `/admin/traces` (роутер `app/llm/admin_router.py`) |

## Файлы

| Файл | Описание |
|------|----------|
| `schemas.py` | Create/Read/Update для всех сущностей + UserAdminRead/Update |
| `service.py` | CRUD-сервисы (7 классов) |
| `router.py` | 31 HTTP-эндпоинт |
| `seed.py` | Загрузка из JSON, идемпотентный |
| `seed_data/` | JSON-файлы с начальными данными |
