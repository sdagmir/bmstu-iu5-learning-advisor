# users — Профиль студента

## Что делает

Управление профилем, оценками по дисциплинам, пройденными ЦК, нагрузкой.
Автоматическое вычисление параметров X5-X12 из данных студента.

## Поток данных

```
Студент вводит:
  X1-X4 (цель, семестр, ТП, нагрузка) → PATCH /users/me
  Оценки по дисциплинам (2-5)         → PUT /users/me/grades
  Пройденные ЦК (галочки)             → POST/DELETE /users/me/completed-ck

Система вычисляет (ProfileBuilder):
  X5  completed_ck_ml      ← есть ЦК category=ml
  X6  ck_dev_status        ← 0 dev→no, 1→partial, 2+→yes
  X7  completed_ck_security← есть ЦК category=security
  X8  completed_ck_testing ← есть ЦК category=testing
  X9  weak_math            ← средняя оценка мат. дисциплин < 4.0
  X10 weak_programming     ← средняя оценка прогр. дисциплин < 4.0
  X11 coverage             ← (комп. студента ∩ целевые) / целевые
  X12 ck_count_in_category ← 3+ ЦК в одной категории → many
```

## Ключевая логика

- **Оценки вместо «слабых предметов»**: студент вводит оценки 2-5, система сама определяет слабые стороны по средней в категории
- **Coverage (X11)**: компетенции из дисциплин до текущего семестра + ЦК, минус дисциплины с оценкой 2
- **Нагрузка**: обязательные + элективные е.з. по семестрам + ЦК (2 е.з.) + Технопарк (6 е.з.)

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/users/me` | Текущий профиль |
| PATCH | `/users/me` | Обновление X1-X4 |
| GET | `/users/me/workload` | Нагрузка: е.з. по семестрам + ЦК + ТП |
| GET | `/users/me/coverage` | Покрытие компетенций: have vs needed для радара |
| GET | `/users/me/completed-ck` | Список пройденных ЦК |
| POST | `/users/me/completed-ck` | Отметить ЦК пройденным |
| DELETE | `/users/me/completed-ck/{id}` | Убрать ЦК |
| GET | `/users/me/grades` | Оценки по дисциплинам |
| PUT | `/users/me/grades` | Массовая замена оценок |

## Файлы

| Файл | Описание |
|------|----------|
| `profile_builder.py` | Автовычисление X5-X12 из БД, маппинг CareerGoal → CareerDirection |
| `workload.py` | Расчёт е.з. по семестрам, TECHNOPARK_CREDITS=6 |
| `service.py` | CRUD: профиль, пройденные ЦК, оценки |
| `schemas.py` | UserRead, ProfileUpdate, GradeRead, CompletedCKRead и др. |
| `router.py` | 8 HTTP-эндпоинтов |
