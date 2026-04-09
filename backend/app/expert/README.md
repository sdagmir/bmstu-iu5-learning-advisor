# expert — Экспертная система

## Что делает

Ядро РС ИТО. 52 правила «если-то» в 7 группах → персональные рекомендации.
Профиль X1-X12 вычисляется автоматически через ProfileBuilder.

## Архитектура

```
StudentProfile (X1-X12)        ← ProfileBuilder (автоматически из БД)
        ↓
  PythonRuleEngine             ← Protocol ExpertEngine (заменяем на КЭСМИ)
        ↓
  evaluate_condition()         ← JSON-интерпретатор (10 операторов)
        ↓
  List[Recommendation] (Y1-Y6) + EvaluationTrace
```

## Правила в JSON (DB-driven)

```json
{
  "condition": {"all": [
    {"param": "career_goal", "op": "eq", "value": "ml"},
    {"param": "semester", "op": "gte", "value": 4}
  ]},
  "recommendation": {
    "category": "ck_course",
    "title": "Инженер машинного обучения",
    "priority": "high",
    "reasoning": "Карьерная цель ML, семестр позволяет"
  }
}
```

Добавить правило = `POST /admin/rules` с JSON. Перезапуск не нужен.

## Операторы условий

`eq` `neq` `gt` `gte` `lt` `lte` `in` `not_in` `lookup_eq` `lookup_neq`

## 7 групп правил (52 шт.)

| Группа | Кол-во | Выход | Что рекомендует |
|--------|--------|-------|-----------------|
| Программы ЦК | 19 | Y1 | Конкретные курсы ЦК |
| Базовые/универсальные | 3 | Y1 | Общие ЦК для всех целей |
| Технопарк | 8 | Y2 | Оптимальный трек ТП |
| Фокус в дисциплинах | 11 | Y3 | На что делать упор |
| Курсовые | 2 | Y4 | Тема курсовой |
| Предупреждения | 5 | Y5 | Риски перегрузки и др. |
| Стратегия | 4 | Y6 | Общий план действий |

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/expert/my-recommendations` | Рекомендации с автопрофилем (основной для фронта) |
| POST | `/expert/evaluate` | Рекомендации по произвольному профилю (what-if) |
| POST | `/expert/evaluate/debug` | Трассировка ЭС (admin) |

## Файлы

| Файл | Описание |
|------|----------|
| `evaluator.py` | Интерпретатор JSON-условий, 10 операторов |
| `engine.py` | PythonRuleEngine + EvaluationTrace |
| `rules_data.py` | 52 правила для seed |
| `schemas.py` | StudentProfile (X1-X12), Recommendation |
| `service.py` | Обёртка движка, seed/DB загрузка |
| `protocols.py` | ExpertEngine Protocol (для замены на КЭСМИ) |
| `router.py` | 3 эндпоинта |
