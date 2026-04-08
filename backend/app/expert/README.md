# expert — Экспертная система

## Что делает
Ядро РС ИТО. 52 правила «если-то» → персональные рекомендации по профилю студента.

## Архитектура
```
StudentProfile (X1-X12)
        ↓
  PythonRuleEngine          ← Protocol ExpertEngine
        ↓                      (заменяем на КЭСМИ)
  evaluate_condition()      ← JSON-интерпретатор
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
    "priority": "high"
  }
}
```
Добавить правило = `POST /admin/rules` с JSON. Перезапуск не нужен.

## Операторы условий
`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `lookup_eq`, `lookup_neq`

## 7 групп правил
1. Программы ЦК (19) → Y1
2. Базовые/универсальные (3) → Y1
3. Технопарк (8) → Y2
4. Фокус в дисциплинах (11) → Y3
5. Курсовые (2) → Y4
6. Предупреждения (5) → Y5
7. Стратегия (4) → Y6

## Файлы
- `evaluator.py` — интерпретатор JSON-условий
- `engine.py` — движок + EvaluationTrace
- `rules_data.py` — 52 правила для seed
- `schemas.py` — StudentProfile, Recommendation
- `service.py` — тонкая обёртка, seed/DB загрузка
- `protocols.py` — ExpertEngine Protocol
