# API Reference -- РС ИТО Backend

Base URL: `/api/v1`

---

## Оглавление

- [Аутентификация и токены](#аутентификация-и-токены)
- [Формат ошибок](#формат-ошибок)
- [Перечисления (Enums)](#перечисления-enums)
- [Auth](#auth----apiv1auth)
- [Users](#users----apiv1users)
- [Catalog](#catalog----apiv1catalog)
- [Expert](#expert----apiv1expert)
- [Chat](#chat----apiv1chat)
- [RAG](#rag----apiv1rag)
- [Admin](#admin----apiv1admin)

---

## Аутентификация и токены

| Параметр | Значение |
|----------|----------|
| Схема | OAuth2 Bearer |
| Алгоритм | HS256 |
| Access token TTL | 1800 сек (30 мин) |
| Refresh token TTL | 2 592 000 сек (30 дней) |

**Заголовок запроса:**

```
Authorization: Bearer <access_token>
```

**Структура access-токена (JWT payload):**

```json
{
  "sub": "<user_id>",   // UUID
  "role": "student",    // "student" | "admin"
  "type": "access",
  "iat": 1712600000,
  "exp": 1712601800
}
```

**Refresh-токен:** 64-символьная hex-строка. При каждом refresh старый токен отзывается, выдается новая пара.

**Поведение при невалидном токене:**
- Отсутствует заголовок `Authorization` -> `401`
- Токен просрочен -> `401`
- Токен подделан/повреждён -> `401`
- Пользователь деактивирован -> `401`
- Роль не admin (на admin-эндпоинтах) -> `403`

---

## Формат ошибок

Все доменные ошибки возвращаются в едином формате:

```json
{
  "error": {
    "code": "NotFoundError",
    "message": "Rule '550e8400-...' not found"
  }
}
```

### Таблица кодов

| HTTP | code | Когда |
|------|------|-------|
| 401 | `UnauthorizedError` | Нет/невалидный токен, неверный логин/пароль, просроченный refresh |
| 403 | `ForbiddenError` | Нет прав (не admin) |
| 404 | `NotFoundError` | Сущность не найдена по ID |
| 409 | `ConflictError` | Дубликат (email, tag, number) |
| 422 | `ValidationError` | Невалидные данные (Pydantic) |
| 502 | `UpstreamError` | Внешний сервис недоступен (LLM, Qdrant, embeddings) |
| 500 | `InternalError` | Необработанная ошибка сервера |

### Pydantic Validation (422)

FastAPI/Pydantic возвращает собственный формат 422, отличный от доменного:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "semester"],
      "msg": "Input should be greater than or equal to 1",
      "input": 0
    }
  ]
}
```

Фронт должен обрабатывать **оба** формата 422: `{ error: {...} }` (доменный) и `{ detail: [...] }` (Pydantic).

---

## Перечисления (Enums)

### CareerGoal -- X1: карьерная цель

| Значение | Описание |
|----------|----------|
| `ml` | Machine Learning |
| `backend` | Backend-разработка |
| `frontend` | Frontend-разработка |
| `cybersecurity` | Кибербезопасность |
| `system` | Системное программирование |
| `devops` | DevOps |
| `mobile` | Мобильная разработка |
| `gamedev` | Разработка игр |
| `qa` | Тестирование |
| `analytics` | Аналитика данных |
| `undecided` | Не определился |

### TechparkStatus -- X3: статус Технопарка

| Значение | Описание |
|----------|----------|
| `none` | Не участвует |
| `backend` | Backend-трек |
| `frontend` | Frontend-трек |
| `ml` | ML-трек |
| `mobile` | Mobile-трек |

### WorkloadPref -- X4: предпочтение нагрузки

| Значение | Описание |
|----------|----------|
| `light` | Лёгкая |
| `normal` | Обычная |
| `intensive` | Интенсивная |

### UserRole

| Значение | Описание |
|----------|----------|
| `student` | Студент |
| `admin` | Администратор |

### CKDevStatus -- X6: статус программ ЦК по разработке

| Значение | Описание |
|----------|----------|
| `yes` | Пройдены |
| `no` | Не пройдены |
| `partial` | Частично |

### CoverageLevel -- X11: покрытие целевого профиля

| Значение | Описание |
|----------|----------|
| `low` | < 30% |
| `medium` | 30-70% |
| `high` | > 70% |

### CKCategoryCount -- X12: кол-во программ ЦК одной категории

| Значение | Описание |
|----------|----------|
| `few` | 0-2 программы |
| `many` | 3+ программы |

### CompetencyCategory

`programming` | `math` | `data` | `ml` | `engineering` | `networks` | `system` | `applied`

### DisciplineType

`mandatory` | `elective` | `choice`

### CKCourseCategory

`ml` | `development` | `security` | `testing` | `management` | `other`

### RuleGroup

`ck_programs` | `basic_universal` | `technopark` | `discipline_focus` | `coursework` | `warnings` | `strategy`

### RecommendationCategory

`ck_course` | `technopark` | `focus` | `coursework` | `warning` | `strategy`

### RecommendationPriority

`high` | `medium` | `low`

---

## Auth -- `/api/v1/auth`

Все эндпоинты публичные (без токена).

---

### `POST /auth/register`

Регистрация нового пользователя. Возвращает пару токенов сразу.

**Request:**

```json
{
  "email": "student@bmstu.ru",
  "password": "securepass123"
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| email | string | Валидный email | да |
| password | string | 8-128 символов | да |

**Response `201`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer"
}
```

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 409 | `ConflictError` | Email уже зарегистрирован |
| 422 | -- | Невалидный email или пароль < 8 / > 128 символов |

---

### `POST /auth/login`

Вход по email/пароль.

**Request:**

```json
{
  "email": "student@bmstu.ru",
  "password": "securepass123"
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| email | string | Валидный email | да |
| password | string | max 128 символов | да |

**Response `200`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "a1b2c3d4e5f6...",
  "token_type": "bearer"
}
```

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Неверный email или пароль |
| 401 | `UnauthorizedError` | Аккаунт деактивирован |
| 422 | -- | Невалидный формат email |

> Сообщение при ошибке одинаковое (`"Invalid email or password"`) -- нельзя узнать, существует ли email.

---

### `POST /auth/demo-login`

Один клик — вход в демо-аккаунт (для защиты диплома). Активен только при `DEMO_ACCOUNT_ENABLED=true` в окружении сервера.

**Request:** пустое тело.

**Response `200`:** `TokenResponse` (как у `/login`).

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 404 | `NotFoundError` | Демо-аккаунт выключен (`DEMO_ACCOUNT_ENABLED=false`) |
| 401 | `UnauthorizedError` | Аккаунт не засеян / отключён |

> Кнопка «Демо для комиссии» на фронте может быть всегда видна — при выключенном флаге сервер вернёт 404 и фронт должен молча скрыть кнопку или показать «недоступно».

---

### `POST /auth/refresh`

Обновление пары токенов. Старый refresh-токен отзывается.

**Request:**

```json
{
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Response `200`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "f6e5d4c3b2a1...",
  "token_type": "bearer"
}
```

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Токен невалидный, просроченный или уже использованный |
| 401 | `UnauthorizedError` | Аккаунт деактивирован |

> Refresh-токен одноразовый. После использования клиент обязан сохранить новый.

---

### `POST /auth/logout`

Отзыв refresh-токена (инвалидация сессии).

**Request:**

```json
{
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Response:** `204 No Content` (пустое тело)

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Токен невалидный |

---

## Users -- `/api/v1/users`

Требует `Authorization: Bearer <access_token>`.

---

### `GET /users/me`

Текущий профиль пользователя.

**Response `200`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@bmstu.ru",
  "role": "student",
  "is_active": true,
  "semester": 5,
  "career_goal": "backend",
  "technopark_status": "none",
  "workload_pref": "normal",
  "created_at": "2026-04-01T12:00:00"
}
```

| Поле | Тип | Nullable | Описание |
|------|-----|----------|----------|
| id | UUID | нет | |
| email | string | нет | |
| role | UserRole | нет | `"student"` или `"admin"` |
| is_active | bool | нет | |
| semester | int | да | 1-8, null если не заполнено |
| career_goal | CareerGoal | да | null если не выбрано |
| technopark_status | TechparkStatus | да | |
| workload_pref | WorkloadPref | да | |
| created_at | datetime | нет | ISO 8601 |

**Ошибки:** `401`

---

### `PATCH /users/me`

Обновление профиля. Передавать только изменяемые поля.

**Request:**

```json
{
  "semester": 6,
  "career_goal": "ml"
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| semester | int \| null | 1-8 | нет |
| career_goal | CareerGoal \| null | enum | нет |
| technopark_status | TechparkStatus \| null | enum | нет |
| workload_pref | WorkloadPref \| null | enum | нет |

**Response `200`:** Обновлённый `UserRead` (полный объект).

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 422 | -- | semester вне диапазона 1-8, невалидный enum |

### `GET /users/me/completed-ck`

Список пройденных программ ЦК текущего студента.

**Response `200`:**

```json
[
  {
    "ck_course_id": "uuid",
    "ck_course_name": "Инженер машинного обучения",
    "ck_course_category": "ml",
    "completed_at": "2026-03-15T10:00:00"
  }
]
```

**Ошибки:** `401`

---

### `POST /users/me/completed-ck`

Отметить ЦК как пройденную.

**Request:**

```json
{
  "ck_course_id": "uuid"
}
```

**Response `201`:** `CompletedCKRead`

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 404 | `NotFoundError` | ЦК курс не найден |
| 409 | `ConflictError` | Уже отмечен как пройденный |

---

### `DELETE /users/me/completed-ck/{ck_course_id}`

Убрать ЦК из пройденных.

**Response:** `204 No Content`

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 404 | `NotFoundError` | Запись не найдена |

---

### `GET /users/me/grades`

Оценки текущего студента по дисциплинам.

**Response `200`:**

```json
[
  {
    "discipline_id": "uuid",
    "discipline_name": "Математический анализ",
    "grade": 4
  }
]
```

**Ошибки:** `401`

---

### `PUT /users/me/grades`

Полная замена оценок по дисциплинам. Передать пустой массив для сброса.

**Request:**

```json
{
  "grades": [
    { "discipline_id": "uuid", "grade": 5 },
    { "discipline_id": "uuid", "grade": 3 }
  ]
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| grades[].discipline_id | UUID | Должен существовать | да |
| grades[].grade | int | 2-5 | да |

**Response `200`:** `GradeRead[]`

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 404 | `NotFoundError` | Дисциплина не найдена |
| 422 | -- | grade вне 2-5 |

---

### `GET /users/me/coverage`

Покрытие компетенций для радара `/coverage` фронтенда. Возвращает плоский список компетенций (объединение «имею» и «нужно для цели») с флагами и общий процент покрытия.

**Response `200`:**

```json
{
  "items": [
    {
      "competency_id": "550e8400-...",
      "name": "Основы Python",
      "category": "programming",
      "has": true,
      "needed": true
    },
    {
      "competency_id": "660e8400-...",
      "name": "Линейная алгебра",
      "category": "math",
      "has": false,
      "needed": true
    }
  ],
  "coverage_percent": 64.3
}
```

**Логика:**

- `needed` — целевые компетенции карьерного направления (по `career_goal` пользователя). Если `career_goal = undecided` или не задано — пустой набор.
- `has` — компетенции из пройденных ЦК + дисциплин с оценкой ≥ 4.
- В `items` попадают только компетенции, где `has` или `needed` (либо оба) — т.е. объединение, не пересечение.
- `coverage_percent = 100 × |has ∩ needed| / |needed|`, округлено до 1 знака. Если `needed` пуст — `0.0`.

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |

---

### `GET /users/me/workload`

Расчёт учебной нагрузки в единицах занятости (е.з.).

**Response `200`:**

```json
{
  "current_semester": 5,
  "semesters": [
    {
      "semester": 1,
      "mandatory_credits": 30,
      "elective_credits": 0,
      "total_curriculum": 30
    },
    {
      "semester": 2,
      "mandatory_credits": 28,
      "elective_credits": 4,
      "total_curriculum": 32
    }
  ],
  "completed_ck_credits": 4,
  "technopark_credits": 6,
  "total_extra_credits": 10
}
```

| Поле | Описание |
|------|----------|
| semesters | Нагрузка по семестрам из учебного плана |
| mandatory_credits | Обязательные дисциплины (е.з.) |
| elective_credits | Элективные + по выбору (е.з.) |
| completed_ck_credits | Суммарные е.з. пройденных ЦК (каждый ЦК = 2 е.з.) |
| technopark_credits | Е.з. Технопарка (6 е.з. если записан, иначе 0) |
| total_extra_credits | ЦК + Технопарк |

**Ошибки:** `401`

---

## Catalog -- `/api/v1/catalog`

Публичный каталог для студентов (read-only). Требует `Authorization: Bearer <access_token>`.

---

### `GET /catalog/disciplines`

Каталог дисциплин. Фронт использует для формы ввода оценок.

**Query:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| semester_max | int \| null | null | Показать дисциплины до указанного семестра (включительно) |

Пример: `GET /catalog/disciplines?semester_max=4` — дисциплины 1-4 семестров.

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "name": "Алгоритмы и структуры данных",
    "semester": 3,
    "credits": 5,
    "type": "mandatory",
    "control_form": "exam",
    "department": "ИУ5",
    "competencies": [
      { "id": "uuid", "tag": "algo", "name": "Алгоритмы", "category": "programming" }
    ]
  }
]
```

**Ошибки:** `401`

---

### `GET /catalog/ck-courses`

Каталог программ цифровой кафедры. Фронт использует для чеклиста пройденных ЦК.

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "name": "Инженер машинного обучения",
    "description": "Базовый курс...",
    "category": "ml",
    "credits": 2,
    "competencies": [ /* CompetencyShort[] */ ],
    "prerequisites": [ /* CompetencyShort[] */ ]
  }
]
```

**Ошибки:** `401`

---

## Expert -- `/api/v1/expert`

Требует `Authorization: Bearer <access_token>`.

---

### `GET /expert/my-recommendations`

Рекомендации для текущего пользователя. **Профиль X1-X12 вычисляется автоматически** из данных в БД (пройденные ЦК, слабые предметы, дисциплины).

**Response `200`:** `Recommendation[]` (формат как у `/evaluate`)

**Ошибки:** `401`

> Основной эндпоинт для фронта. Студент заполняет профиль и отмечает ЦК/слабые предметы, рекомендации считаются сами.

---

### `GET /expert/recommendations/history`

Лента прошлых снапшотов рекомендаций. Снапшоты автоматически создаются при изменении X1–X4 (PATCH /users/me) — фиксируется список рекомендаций и краткое описание изменений.

**Query:** `offset` (default 0), `limit` (default 50, max 100)

**Response `200`:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-05-04T12:00:00+00:00",
    "recommendations": [
      {
        "rule_id": "R1",
        "category": "ck_course",
        "title": "Рекомендуется программа ЦК «Введение в ML»",
        "priority": "high",
        "reasoning": "Карьерная цель ML, программа ещё не пройдена",
        "competency_gap": "ml_basics"
      }
    ],
    "profile_change_summary": "Цель: backend → ml; Семестр: 4 → 5"
  }
]
```

**Поведение:**

- Сортировка по `created_at` (сначала свежие).
- Snapshot создаётся только при фактическом изменении X1–X4 и только если набор `rule_id`-ов отличается от последнего сохранённого (no-op обновления игнорируются).
- `profile_change_summary` — человекочитаемая строка вида «Поле: старое → новое; …». Может быть `null` для исторических записей.

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |

---

### `POST /expert/evaluate`

Получение рекомендаций на основе профиля студента.

**Request -- StudentProfile:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "semester": 5,
  "career_goal": "ml",
  "technopark_status": "none",
  "workload_pref": "normal",
  "completed_ck_ml": false,
  "ck_dev_status": "no",
  "completed_ck_security": false,
  "completed_ck_testing": false,
  "weak_math": false,
  "weak_programming": false,
  "coverage": "low",
  "ck_count_in_category": "few"
}
```

| Поле | Тип | По умолчанию | Описание |
|------|-----|-------------|----------|
| user_id | UUID | -- | Обязательное |
| semester | int | -- | 1-8, обязательное |
| career_goal | CareerGoal | -- | Обязательное |
| technopark_status | TechparkStatus | -- | Обязательное |
| workload_pref | WorkloadPref | -- | Обязательное |
| completed_ck_ml | bool | `false` | X5: пройдены ли ЦК по ML |
| ck_dev_status | CKDevStatus | `"no"` | X6: статус ЦК по разработке |
| completed_ck_security | bool | `false` | X7: пройдены ли ЦК по безопасности |
| completed_ck_testing | bool | `false` | X8: пройдены ли ЦК по тестированию |
| weak_math | bool | `false` | X9: слабая математика |
| weak_programming | bool | `false` | X10: слабое программирование |
| coverage | CoverageLevel | `"low"` | X11: покрытие профиля |
| ck_count_in_category | CKCategoryCount | `"few"` | X12: кол-во ЦК в категории |

**Response `200`:**

```json
[
  {
    "rule_id": "R1",
    "category": "ck_course",
    "title": "Рекомендуется программа ЦК «Введение в ML»",
    "priority": "high",
    "reasoning": "Карьерная цель ML, программа ещё не пройдена",
    "competency_gap": "ml_basics"
  },
  {
    "rule_id": "R15",
    "category": "technopark",
    "title": "Рекомендуется ML-трек Технопарка",
    "priority": "medium",
    "reasoning": "Оптимальный трек для ML-направления",
    "competency_gap": null
  }
]
```

**Recommendation:**

| Поле | Тип | Nullable |
|------|-----|----------|
| rule_id | string | нет |
| category | RecommendationCategory | нет |
| title | string | нет |
| priority | RecommendationPriority | нет |
| reasoning | string | нет |
| competency_gap | string | да |

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 422 | -- | Невалидный профиль (semester, enums) |

---

### `POST /expert/evaluate/debug`

То же, что `/evaluate`, но возвращает трассировку. **Только для admin.**

**Request:** То же, что `/evaluate`.

**Response `200`:**

```json
{
  "recommendations": [ /* ...Recommendation[] */ ],
  "trace": {
    "profile_snapshot": { /* StudentProfile как dict */ },
    "total_checked": 52,
    "total_fired": 8,
    "fired_rule_ids": ["R1", "R15", "R34", "R40", "R41", "R48", "R50", "R52"],
    "entries": [
      {
        "rule": "R1",
        "name": "ML новичок -> ЦК по ML",
        "group": "ck_programs",
        "fired": true,
        "skipped_reason": null
      },
      {
        "rule": "R2",
        "name": "ML продвинутый -> углублённый ЦК",
        "group": "ck_programs",
        "fired": false,
        "skipped_reason": "condition not met"
      }
    ]
  }
}
```

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 422 | -- | Невалидный профиль |

---

## Chat -- `/api/v1/chat`

Требует `Authorization: Bearer <access_token>`.

---

### `POST /chat/message`

Отправка сообщения ИИ-ассистенту. LLM сам решает, вызвать ЭС или RAG.

**Request:**

```json
{
  "message": "Какие курсы мне взять для ML?",
  "history": [
    { "role": "user", "content": "Привет" },
    { "role": "assistant", "content": "Здравствуйте! Чем могу помочь?" }
  ]
}
```

| Поле | Тип | По умолчанию | Описание |
|------|-----|-------------|----------|
| message | string | -- | Обязательное |
| history | ChatMessage[] | `[]` | Предыдущие сообщения диалога |

**ChatMessage:**

| Поле | Тип | Допустимые значения |
|------|-----|---------------------|
| role | string | `"user"`, `"assistant"` |
| content | string | Текст сообщения |

**Response `200`:**

```json
{
  "reply": "На основе вашего профиля рекомендую...",
  "debug": null
}
```

**Поведение:**
- LLM вызывает до 3 tool-раундов (function calling)
- Доступные функции: `get_recommendations`, `recalculate_with_changes`, `search_knowledge`
- Через чат можно менять: `career_goal`, `technopark_status`, `workload_pref`
- Если RAG недоступен -- LLM получает fallback-сообщение, чат продолжает работать
- История хранится на клиенте, сервер stateless

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 502 | `UpstreamError` | LLM-сервис (OpenRouter) недоступен |

---

### `POST /chat/message/debug`

То же, но возвращает отладочные данные. **Только для admin.**

**Request:** То же, что `/chat/message`.

**Response `200`:**

```json
{
  "reply": "На основе вашего профиля рекомендую...",
  "debug": {
    "rules_fired": ["R1", "R15", "R34"],
    "rag_chunks": ["chunk about ML courses...", "chunk about prerequisites..."],
    "tool_calls": [
      { "function": "get_recommendations", "arguments": {} },
      { "function": "search_knowledge", "arguments": { "query": "ML курсы" } }
    ],
    "profile_changes": { "career_goal": "ml" }
  }
}
```

**DebugInfo:**

| Поле | Тип | Описание |
|------|-----|----------|
| rules_fired | string[] | ID сработавших правил ЭС |
| rag_chunks | string[] | Найденные фрагменты из базы знаний |
| tool_calls | object[] | Вызовы функций LLM |
| profile_changes | object | Изменения профиля в рамках диалога |

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 502 | `UpstreamError` | LLM недоступен |

---

## RAG -- `/api/v1/rag`

Требует `Authorization: Bearer <access_token>`.

---

### `POST /rag/search`

Семантический поиск по базе знаний (hybrid: dense + BM25 -> RRF).

**Request:**

```json
{
  "query": "требования к курсовой по ML",
  "top_k": 5
}
```

| Поле | Тип | По умолчанию | Описание |
|------|-----|-------------|----------|
| query | string | -- | Обязательное |
| top_k | int | `5` | Кол-во результатов |

**Response `200`:**

```json
[
  {
    "content": "Курсовая работа по направлению ML должна...",
    "source": "docs/coursework_requirements.md",
    "score": 0.87
  }
]
```

| Поле | Тип | Описание |
|------|-----|----------|
| content | string | Текст фрагмента |
| source | string | Источник документа |
| score | float | Релевантность (0-1, выше = лучше) |

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 502 | `UpstreamError` | Qdrant или embedding-сервис недоступен |

---

### `GET /rag/documents` (admin)

Список индексированных источников с агрегатами.

**Query:** `offset` (default 0), `limit` (default 50, max 100)

**Response `200`:**

```json
[
  {
    "source": "docs/coursework_requirements.md",
    "chunks_count": 12,
    "indexed_at": "2026-05-04T10:30:00+00:00"
  }
]
```

| Поле | Тип | Nullable | Описание |
|------|-----|----------|----------|
| source | string | нет | Идентификатор документа (путь) |
| chunks_count | int | нет | Количество чанков в Qdrant |
| indexed_at | datetime | да | Время последней индексации (null для документов, проиндексированных до версии 0.x) |

**Поведение:**

- Сортировка по `source` (алфавитно), пагинация — по уникальным источникам, не чанкам.
- Конец списка: `len(response) < limit`.

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 502 | `UpstreamError` | Qdrant недоступен |

---

### `POST /rag/documents` (admin)

Загрузка документа в базу знаний. Текст разбивается на чанки, генерируются эмбеддинги.

**Request:**

```json
{
  "source": "docs/coursework_requirements.md",
  "text": "Полный текст документа..."
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| source | string | Идентификатор документа (может быть путь) |
| text | string | Полный текст документа |

**Response `201`:**

```json
{
  "source": "docs/coursework_requirements.md",
  "chunks_count": 12
}
```

**Поведение:** При повторной загрузке с тем же `source` старые чанки удаляются, загружаются новые.

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 502 | `UpstreamError` | Qdrant или embedding-сервис недоступен |

---

### `DELETE /rag/documents/{source}` (admin)

Удаление документа и всех его чанков.

**Path:** `source` может содержать `/` (path converter).

**Response:** `204 No Content`

**Поведение:** Если документ не найден -- молча ничего не происходит (идемпотентно).

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 502 | `UpstreamError` | Qdrant недоступен |

---

### `GET /rag/stats` (admin)

Статистика базы знаний.

**Response `200`:**

```json
{
  "total_chunks": 156
}
```

**Ошибки:** `401`, `403`

---

## Admin -- `/api/v1/admin`

**Все эндпоинты требуют роль `admin`.**

### LLM-трейсы -- `/admin/traces`

Журнал запросов к LLM-чату. Каждый вызов `/chat/message` и `/chat/message/debug` пишет запись с request, response, отладкой, латентностью и статусом.

#### `GET /admin/traces`

**Query:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| user_id | UUID \| null | null | Фильтр по пользователю |
| date_from | datetime \| null | null | С какого момента (включительно) |
| date_to | datetime \| null | null | По какой момент (включительно) |
| offset | int | 0 | -- |
| limit | int | 50 | 1-100 |

**Response `200`:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2026-05-04T17:00:00+00:00",
    "user_email": "student@bmstu.ru",
    "endpoint": "message",
    "latency_ms": 1234,
    "status": "ok",
    "rules_fired_count": 3,
    "request_preview": "Какие курсы ЦК подойдут для ML?"
  }
]
```

#### `GET /admin/traces/{trace_id}`

**Response `200`:**

```json
{
  "id": "550e8400-...",
  "created_at": "2026-05-04T17:00:00+00:00",
  "user_id": "660e8400-...",
  "user_email": "student@bmstu.ru",
  "endpoint": "message",
  "request_message": "Какие курсы ЦК подойдут для ML?",
  "response_text": "На основе вашего профиля...",
  "debug": {
    "rules_fired": ["R1", "R15"],
    "rag_chunks": ["..."],
    "tool_calls": [{"function": "get_recommendations", "args": {}}],
    "profile_changes": {}
  },
  "latency_ms": 1234,
  "status": "ok",
  "model_name": "google/gemini-2.5-flash"
}
```

**Поведение:**

- `debug` отдаётся для всех endpoint'ов, но для `message` (без `/debug`) обычно `null`, потому что debug-информация в студенческом чате не собирается.
- `status` — `ok` / `error` / `timeout` (при сбое OpenRouter).
- Запись в журнал — фоновая задача (BackgroundTasks), не блокирует ответ клиенту.

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 404 | `NotFoundError` | Trace не найден (для `/{id}`) |

---

### Пагинация

Все GET-списки поддерживают query-параметры:

| Параметр | Тип | По умолчанию | Ограничения |
|----------|-----|-------------|-------------|
| offset | int | `0` | >= 0 |
| limit | int | `50` (правила: `100`) | 1-100 |

Пример: `GET /admin/competencies?offset=10&limit=20`

Ответ -- плоский массив. Общее количество не возвращается (для UI с бесконечным скроллом: если `len(result) < limit`, записи закончились).

---

### Пользователи -- `/admin/users`

#### `GET /admin/users`

**Query:** `offset`, `limit` (default 50)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "email": "student@bmstu.ru",
    "role": "student",
    "is_active": true,
    "semester": 5,
    "career_goal": "ml",
    "technopark_status": "none",
    "workload_pref": "normal",
    "created_at": "2026-04-01T12:00:00"
  }
]
```

---

#### `GET /admin/users/{user_id}`

**Response `200`:** `UserAdminRead` (как в списке)

**Ошибки:** `404`

---

#### `GET /admin/users/{user_id}/profile-snapshot`

Полный X1–X12 профиль студента — для кнопки «Загрузить из студента» в sandbox конструктора правил. Работает поверх той же `build_student_profile`, что и `/expert/my-recommendations`.

**Response `200`:** `StudentProfile` (как в `POST /expert/evaluate`).

**Ошибки:**

| HTTP | code | Условие |
|------|------|---------|
| 401 | `UnauthorizedError` | Невалидный токен |
| 403 | `ForbiddenError` | Не admin |
| 404 | `NotFoundError` | Пользователь не найден |

---

#### `PATCH /admin/users/{user_id}`

Обновление роли и/или статуса активности.

**Request:**

```json
{
  "role": "admin",
  "is_active": false
}
```

| Поле | Тип | Обязательное |
|------|-----|--------------|
| role | UserRole \| null | нет |
| is_active | bool \| null | нет |

**Response `200`:** обновлённый `UserAdminRead`

**Ошибки:** `404`, `422`

---

### Компетенции -- `/admin/competencies`

#### `GET /admin/competencies`

**Query:** `offset`, `limit` (default 50)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "tag": "py_basics",
    "name": "Основы Python",
    "category": "programming"
  }
]
```

---

#### `POST /admin/competencies`

**Request:**

```json
{
  "tag": "py_basics",
  "name": "Основы Python",
  "category": "programming"
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| tag | string | max 50 | да |
| name | string | max 255 | да |
| category | CompetencyCategory | enum | да |

**Response:** `201` -- `CompetencyRead`

**Ошибки:** `409` (дубликат tag)

---

#### `PATCH /admin/competencies/{competency_id}`

**Request:** Любые поля из `CompetencyCreate`, все опциональные.

**Response:** `200` -- обновлённый `CompetencyRead`

**Ошибки:** `404`, `409`, `422`

---

#### `DELETE /admin/competencies/{competency_id}`

**Response:** `204 No Content`

**Ошибки:** `404`

---

### Дисциплины -- `/admin/disciplines`

#### `GET /admin/disciplines`

**Query:** `offset`, `limit` (default 50)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "name": "Алгоритмы и структуры данных",
    "semester": 3,
    "credits": 5,
    "type": "mandatory",
    "control_form": "exam",
    "department": "ИУ5",
    "competencies": [
      { "id": "uuid", "tag": "algo", "name": "Алгоритмы", "category": "programming" }
    ]
  }
]
```

---

#### `POST /admin/disciplines`

**Request:**

```json
{
  "name": "Алгоритмы и структуры данных",
  "semester": 3,
  "credits": 5,
  "type": "mandatory",
  "control_form": "exam",
  "department": "ИУ5",
  "competency_ids": ["uuid1", "uuid2"]
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| name | string | max 255 | да |
| semester | int | 1-8 | да |
| credits | int | >= 1 | да |
| type | DisciplineType | enum | да |
| control_form | string | max 50 | да |
| department | string \| null | max 50 | нет |
| competency_ids | UUID[] | Должны существовать | нет (default `[]`) |

**Response:** `201` -- `DisciplineRead`

**Ошибки:** `409`, `422`

---

#### `PATCH /admin/disciplines/{discipline_id}`

**Request:** Все поля опциональные. `competency_ids` при передаче **заменяет** весь список (не добавляет).

**Response:** `200` -- обновлённый `DisciplineRead`

**Ошибки:** `404`, `422`

---

#### `DELETE /admin/disciplines/{discipline_id}`

**Response:** `204 No Content`

**Ошибки:** `404`

---

### Программы ЦК -- `/admin/ck-courses`

#### `GET /admin/ck-courses`

**Query:** `offset`, `limit` (default 50)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "name": "Введение в машинное обучение",
    "description": "Базовый курс по ML...",
    "category": "ml",
    "competencies": [ /* CompetencyRead[] */ ],
    "prerequisites": [ /* CompetencyRead[] */ ]
  }
]
```

---

#### `POST /admin/ck-courses`

**Request:**

```json
{
  "name": "Введение в ML",
  "description": "Базовый курс...",
  "category": "ml",
  "competency_ids": ["uuid1"],
  "prerequisite_ids": ["uuid2"]
}
```

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| name | string | max 255 | да |
| description | string \| null | -- | нет |
| category | CKCourseCategory | enum | да |
| competency_ids | UUID[] | Должны существовать | нет (default `[]`) |
| prerequisite_ids | UUID[] | Должны существовать | нет (default `[]`) |

**Response:** `201` -- `CKCourseRead`

**Ошибки:** `409`, `422`

---

#### `PATCH /admin/ck-courses/{course_id}`

**Request:** Все поля опциональные. `competency_ids`/`prerequisite_ids` при передаче **заменяют** весь список.

**Response:** `200` -- `CKCourseRead`

**Ошибки:** `404`, `422`

---

#### `DELETE /admin/ck-courses/{course_id}`

**Response:** `204 No Content`

**Ошибки:** `404`

---

### Карьерные направления -- `/admin/career-directions`

#### `GET /admin/career-directions`

**Query:** `offset`, `limit` (default 50)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "name": "Machine Learning Engineer",
    "description": "Разработка ML-моделей...",
    "example_jobs": "ML Engineer, Data Scientist",
    "competencies": [ /* CompetencyRead[] */ ]
  }
]
```

---

#### `POST /admin/career-directions`

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| name | string | max 100 | да |
| description | string \| null | -- | нет |
| example_jobs | string \| null | -- | нет |
| competency_ids | UUID[] | Должны существовать | нет (default `[]`) |

**Response:** `201` -- `CareerDirectionRead`

**Ошибки:** `409`, `422`

---

#### `PATCH /admin/career-directions/{direction_id}`

**Request:** Все поля опциональные. `competency_ids` при передаче **заменяет** весь список.

**Response:** `200` -- `CareerDirectionRead`

**Ошибки:** `404`, `422`

---

#### `DELETE /admin/career-directions/{direction_id}`

**Response:** `204 No Content`

**Ошибки:** `404`

---

### Фокусы дисциплин -- `/admin/focus-advices`

#### `GET /admin/focus-advices`

**Query:** `offset`, `limit` (default 50)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "discipline_id": "uuid",
    "career_direction_id": "uuid",
    "focus_advice": "Сделать упор на нейронные сети в лабораторных",
    "reasoning": "Для ML-направления критически важно..."
  }
]
```

---

#### `POST /admin/focus-advices`

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| discipline_id | UUID | Должен существовать | да |
| career_direction_id | UUID | Должен существовать | да |
| focus_advice | string | -- | да |
| reasoning | string \| null | -- | нет |

**Response:** `201` -- `FocusAdviceRead`

**Ошибки:** `409` (дубликат discipline_id + career_direction_id), `422`

---

#### `PATCH /admin/focus-advices/{advice_id}`

| Поле | Тип | Обязательное |
|------|-----|--------------|
| focus_advice | string \| null | нет |
| reasoning | string \| null | нет |

**Response:** `200` -- `FocusAdviceRead`

**Ошибки:** `404`, `422`

---

#### `DELETE /admin/focus-advices/{advice_id}`

**Response:** `204 No Content`

**Ошибки:** `404`

---

### Правила ЭС -- `/admin/rules`

#### `GET /admin/rules`

**Query:** `offset` (default 0), `limit` (default **100**)

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "number": 1,
    "group": "ck_programs",
    "name": "ML новичок -> ЦК по ML",
    "description": "Рекомендация программы ЦК по ML для студентов с целью ML",
    "condition": {
      "all": [
        { "field": "career_goal", "op": "eq", "value": "ml" },
        { "field": "completed_ck_ml", "op": "eq", "value": false }
      ]
    },
    "recommendation": {
      "category": "ck_course",
      "title": "Рекомендуется программа ЦК «Введение в ML»",
      "priority": "high",
      "reasoning": "...",
      "competency_gap": "ml_basics"
    },
    "priority": 0,
    "is_active": true,
    "is_published": true,
    "trigger_count": 42
  }
]
```

`trigger_count` — сколько раз правило сработало в production-движке (только при `GET /expert/my-recommendations`). Preview/sandbox/what-if вызовы счётчик не трогают.

---

#### `POST /admin/rules`

| Поле | Тип | Ограничения | Обязательное |
|------|-----|-------------|--------------|
| number | int | >= 1 | да |
| group | RuleGroup | enum | да |
| name | string | max 255 | да |
| description | string | -- | нет (default `""`) |
| condition | object | JSON-условие | да |
| recommendation | object | JSON-рекомендация | да |
| priority | int | -- | нет (default `0`) |
| is_active | bool | -- | нет (default `true`) |

**Формат condition (JSON):**

```json
// Простое условие
{ "field": "career_goal", "op": "eq", "value": "ml" }

// Комбинация AND
{ "all": [ ...условия ] }

// Комбинация OR
{ "any": [ ...условия ] }

// Вложенные
{
  "all": [
    { "field": "semester", "op": "gte", "value": 5 },
    { "any": [
      { "field": "career_goal", "op": "eq", "value": "ml" },
      { "field": "career_goal", "op": "eq", "value": "analytics" }
    ]}
  ]
}
```

**Доступные операторы:**

| Оператор | Описание | Пример |
|----------|----------|--------|
| `eq` | Равно | `{ "op": "eq", "value": "ml" }` |
| `neq` | Не равно | `{ "op": "neq", "value": "none" }` |
| `gt` | Больше | `{ "op": "gt", "value": 4 }` |
| `gte` | Больше или равно | `{ "op": "gte", "value": 5 }` |
| `lt` | Меньше | `{ "op": "lt", "value": 3 }` |
| `lte` | Меньше или равно | `{ "op": "lte", "value": 6 }` |
| `in` | Входит в список | `{ "op": "in", "value": ["ml","analytics"] }` |
| `not_in` | Не входит в список | `{ "op": "not_in", "value": ["none"] }` |
| `lookup_eq` | Lookup-таблица + равно | `{ "op": "lookup_eq", "value": "ml", "lookup": "tp_map" }` |
| `lookup_neq` | Lookup-таблица + не равно | `{ "op": "lookup_neq", ... }` |

**Формат recommendation (JSON):**

```json
{
  "category": "ck_course",
  "title": "Рекомендуется программа ЦК «Введение в ML»",
  "priority": "high",
  "reasoning": "Карьерная цель {career_goal}, программа не пройдена",
  "competency_gap": "ml_basics"
}
```

> `{career_goal}`, `{career_goal_area}` -- шаблонные переменные, подставляются при срабатывании.

**Response:** `201` -- `RuleRead`

**Ошибки:** `409` (дубликат number), `422`

---

#### `PATCH /admin/rules/{rule_id}`

**Request:** Все поля опциональные (кроме `number` -- не изменяется).

**Response:** `200` -- `RuleRead`

**Ошибки:** `404`, `422`

---

#### `DELETE /admin/rules/{rule_id}`

**Response:** `204 No Content`

**Ошибки:** `404`

---

## Сводка эндпоинтов

| # | Метод | Путь | Доступ | Код |
|---|-------|------|--------|-----|
| 1 | POST | `/auth/register` | public | 201 |
| 2 | POST | `/auth/login` | public | 200 |
| 3 | POST | `/auth/demo-login` | public | 200 |
| 4 | POST | `/auth/refresh` | public | 200 |
| 5 | POST | `/auth/logout` | public | 204 |
| 5 | GET | `/users/me` | user | 200 |
| 6 | PATCH | `/users/me` | user | 200 |
| 7 | GET | `/users/me/coverage` | user | 200 |
| 8 | GET | `/users/me/workload` | user | 200 |
| 9 | GET | `/users/me/completed-ck` | user | 200 |
| 10 | POST | `/users/me/completed-ck` | user | 201 |
| 11 | DELETE | `/users/me/completed-ck/{id}` | user | 204 |
| 12 | GET | `/users/me/grades` | user | 200 |
| 13 | PUT | `/users/me/grades` | user | 200 |
| 14 | GET | `/catalog/disciplines` | user | 200 |
| 15 | GET | `/catalog/ck-courses` | user | 200 |
| 16 | GET | `/expert/my-recommendations` | user | 200 |
| 17 | GET | `/expert/recommendations/history` | user | 200 |
| 18 | POST | `/expert/evaluate` | user | 200 |
| 19 | POST | `/expert/evaluate/debug` | admin | 200 |
| 20 | POST | `/chat/message` | user | 200 |
| 21 | POST | `/chat/message/debug` | admin | 200 |
| 22 | POST | `/rag/search` | user | 200 |
| 23 | GET | `/rag/documents` | admin | 200 |
| 24 | POST | `/rag/documents` | admin | 201 |
| 25 | DELETE | `/rag/documents/{source}` | admin | 204 |
| 26 | GET | `/rag/stats` | admin | 200 |
| 27-28 | GET | `/admin/traces`, `/admin/traces/{id}` | admin | 200 |
| 29-31 | RU | `/admin/users` | admin | -- |
| 32-35 | CRUD | `/admin/competencies` | admin | -- |
| 36-39 | CRUD | `/admin/disciplines` | admin | -- |
| 40-43 | CRUD | `/admin/ck-courses` | admin | -- |
| 44-47 | CRUD | `/admin/career-directions` | admin | -- |
| 48-51 | CRUD | `/admin/focus-advices` | admin | -- |
| 52-55 | CRUD | `/admin/rules` | admin | -- |

**Итого: 57 эндпоинтов** (5 public, 17 user, 35 admin) — `/auth/demo-login` активен только при `DEMO_ACCOUNT_ENABLED=true`, `/admin/users/{id}/profile-snapshot` добавлен.

---

## Рекомендации для фронтенда

### Обработка токенов

1. При `register`/`login` сохранить оба токена (access в память, refresh в httpOnly cookie или localStorage)
2. Access-токен добавлять в `Authorization: Bearer <token>`
3. При получении `401` -- попробовать `POST /auth/refresh`
4. Если refresh тоже вернул `401` -- перенаправить на логин
5. После refresh сохранить **новую пару** (старый refresh-токен невалиден)

### Обработка ошибок

```typescript
// Универсальный обработчик
async function handleResponse(res: Response) {
  if (res.ok) return res.status === 204 ? null : res.json();

  const body = await res.json();

  // Доменная ошибка
  if (body.error) {
    throw new ApiError(res.status, body.error.code, body.error.message);
  }

  // Pydantic validation
  if (body.detail) {
    throw new ValidationError(body.detail);
  }

  throw new Error("Unknown error");
}
```

### История чата

Сервер stateless -- фронт хранит `ChatMessage[]` и отправляет в каждом запросе.

### Автовычисление профиля (X5-X12)

Студент управляет только:
- X1-X4 через `PATCH /users/me` (career_goal, semester, technopark_status, workload_pref)
- Пройденными ЦК через `POST/DELETE /users/me/completed-ck`
- Оценками по дисциплинам через `PUT /users/me/grades`

Параметры X5-X12 **вычисляются автоматически** сервером при вызове `GET /expert/my-recommendations` или `POST /chat/message`:

| Параметр | Как вычисляется |
|----------|-----------------|
| X5 `completed_ck_ml` | Есть пройденный ЦК с `category = "ml"` |
| X6 `ck_dev_status` | 0 dev-ЦК → `no`, 1 → `partial`, 2+ → `yes` |
| X7 `completed_ck_security` | Есть пройденный ЦК с `category = "security"` |
| X8 `completed_ck_testing` | Есть пройденный ЦК с `category = "testing"` |
| X9 `weak_math` | Средняя оценка по дисциплинам с мат. компетенциями < 4.0 |
| X10 `weak_programming` | Средняя оценка по дисциплинам с прогр. компетенциями < 4.0 |
| X11 `coverage` | (комп. студента ∩ целевые) / целевые; дисциплины с оценкой 2 исключаются |
| X12 `ck_count_in_category` | 3+ ЦК в одной категории → `many` |

### Пагинация (админка)

Сервер не возвращает `total_count`. Определение конца списка: если `response.length < limit`, записей больше нет.

### CORS

Разрешённый origin: `http://localhost:3000` (по умолчанию). Настраивается через `CORS_ORIGINS` в .env.
