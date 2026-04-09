# auth — Аутентификация

## Что делает

JWT-аутентификация с refresh token rotation. Две роли: `student`, `admin`.

## Поток

```
register → bcrypt(password) → JWT access (30 мин) + SHA-256(refresh, 30 дней) в БД
login    → timing-safe verify → JWT access + refresh
refresh  → revoke old → issue new pair (одноразовый!)
logout   → revoke refresh
```

## Безопасность

- **bcrypt** 12 раундов, без passlib (напрямую)
- **PyJWT** HS256, без python-jose
- Refresh-токены: `secrets.token_hex(32)` → SHA-256 хеш в БД
- Timing-safe проверка: при неизвестном email используется `_DUMMY_HASH`
- Duplicate email → `IntegrityError` → `409 ConflictError`
- Refresh проверяет `is_active` пользователя
- JWT_SECRET_KEY < 32 символов → приложение не запустится

## API

| Метод | Путь | Код | Описание |
|-------|------|-----|----------|
| POST | `/auth/register` | 201 | Регистрация → пара токенов |
| POST | `/auth/login` | 200 | Вход → пара токенов |
| POST | `/auth/refresh` | 200 | Обновление пары (старый отзывается) |
| POST | `/auth/logout` | 204 | Отзыв refresh-токена |

## Файлы

| Файл | Описание |
|------|----------|
| `security.py` | bcrypt hash/verify, JWT create/decode, refresh token SHA-256 |
| `service.py` | Бизнес-логика: register, login, refresh, logout |
| `schemas.py` | RegisterRequest, LoginRequest, TokenResponse, RefreshRequest |
| `router.py` | 4 HTTP-эндпоинта |
