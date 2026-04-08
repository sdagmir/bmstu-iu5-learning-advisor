# auth — Аутентификация

## Что делает
JWT-аутентификация с refresh token rotation. Две роли: `student`, `admin`.

## Поток
```
register → bcrypt(password) → JWT access + SHA-256(refresh) в БД
login    → verify → JWT access + refresh
refresh  → revoke old → issue new pair
logout   → revoke refresh
```

## Безопасность
- Refresh-токены хранятся как SHA-256 хеш (не сырые)
- Timing-safe проверка пароля (защита от перебора email)
- Race condition на duplicate email → ловим IntegrityError
- Refresh проверяет is_active пользователя

## API
| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация → токены |
| POST | `/auth/login` | Вход → токены |
| POST | `/auth/refresh` | Обновление пары токенов |
| POST | `/auth/logout` | Отзыв refresh-токена |

## Файлы
- `security.py` — bcrypt, JWT, refresh token hashing
- `schemas.py` — Pydantic-модели запросов/ответов
- `service.py` — бизнес-логика
- `router.py` — HTTP-эндпоинты
