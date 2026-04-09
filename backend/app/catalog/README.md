# catalog — Публичный каталог

## Что делает

Read-only доступ к дисциплинам и программам ЦК для студентов.
Фронтенд использует для форм ввода оценок и чеклиста пройденных ЦК.

## Использование на фронте

```
1. GET /users/me → semester = 5
2. GET /catalog/disciplines?semester_max=4 → дисциплины 1-4 семестров
3. Студент вводит оценки → PUT /users/me/grades

4. GET /catalog/ck-courses → каталог ЦК
5. Студент ставит галочки → POST /users/me/completed-ck
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/catalog/disciplines` | Каталог дисциплин (фильтр `semester_max`) |
| GET | `/catalog/ck-courses` | Каталог программ ЦК |

## Файлы

| Файл | Описание |
|------|----------|
| `schemas.py` | DisciplineCatalog, CKCourseCatalog, CompetencyShort |
| `router.py` | 2 эндпоинта |
