from __future__ import annotations

from app.db.models import CareerGoal, TechparkStatus

# R28: оптимальное направление Технопарка для каждой карьерной цели
# Источник: примечание к R28 в МЭС — бэкенд→бэкенд, фронтенд→фронтенд,
# ML→ML, мобильная→мобильная, DevOps→бэкенд, аналитика→ML
GOAL_TO_OPTIMAL_TECHNOPARK: dict[CareerGoal, TechparkStatus | None] = {
    CareerGoal.BACKEND: TechparkStatus.BACKEND,
    CareerGoal.FRONTEND: TechparkStatus.FRONTEND,
    CareerGoal.ML: TechparkStatus.ML,
    CareerGoal.MOBILE: TechparkStatus.MOBILE,
    CareerGoal.DEVOPS: TechparkStatus.BACKEND,
    CareerGoal.ANALYTICS: TechparkStatus.ML,
    CareerGoal.CYBERSECURITY: None,
    CareerGoal.SYSTEM: None,
    CareerGoal.GAMEDEV: None,
    CareerGoal.QA: None,
    CareerGoal.UNDECIDED: None,
}

# R40: название области для рекомендации темы курсовой по карьерной цели
GOAL_TO_COURSEWORK_AREA: dict[CareerGoal, str] = {
    CareerGoal.ML: "машинного обучения и анализа данных",
    CareerGoal.BACKEND: "бэкенд-разработки",
    CareerGoal.FRONTEND: "фронтенд-разработки",
    CareerGoal.CYBERSECURITY: "кибербезопасности",
    CareerGoal.SYSTEM: "системного программирования",
    CareerGoal.DEVOPS: "DevOps и автоматизации инфраструктуры",
    CareerGoal.MOBILE: "мобильной разработки",
    CareerGoal.GAMEDEV: "разработки компьютерных игр",
    CareerGoal.QA: "тестирования ПО",
    CareerGoal.ANALYTICS: "аналитики данных",
    CareerGoal.UNDECIDED: "общей разработки ПО",
}
