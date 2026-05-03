# Конструктор скиллов для Claude Code

Универсальный каталог скиллов для сборки оптимального сетапа агента.
Используй как меню: выбери нужные блоки → установи → работай.

---

## Как пользоваться этим документом

1. Определи тип проекта (фронт, бэк, фуллстек, лендинг, дашборд...)
2. Выбери скиллы из каждой категории по необходимости
3. Установи глобальные (для всех проектов) и локальные (для конкретного)
4. Настрой параметры под свой контекст

### Правило: не ставь всё подряд

Больше скиллов ≠ лучше. Claude Code загружает описания всех скиллов в контекст (~100 токенов каждый).
Оптимум: 5–8 скиллов одновременно. Ставь глобально только то, что нужно ВСЕГДА.

### Куда ставить

```
~/.claude/skills/        — глобально (все проекты)
.claude/skills/          — локально (конкретный проект)
```

### Универсальная команда установки

```bash
# Через npx (если скилл поддерживает)
npx skills add https://github.com/AUTHOR/REPO

# Через plugin marketplace (если доступен как плагин)
/plugin marketplace add AUTHOR/REPO
/plugin install SKILL_NAME@REPO

# Ручная установка (всегда работает)
git clone https://github.com/AUTHOR/REPO /tmp/repo
cp -r /tmp/repo/skills/SKILL_NAME ~/.claude/skills/   # или .claude/skills/
rm -rf /tmp/repo
```

---

## Категория 1: ДИЗАЙН ФРОНТЕНДА

Скиллы которые учат Claude Code генерировать красивый UI вместо generic slop.

### 1.1 Impeccable ⭐⭐⭐⭐⭐

**Назначение:** Базовая дизайн-система + 18 команд для аудита/полировки UI.
**Автор:** Paul Bakaus (Google DevRel) | **Stars:** 19k | **Лицензия:** Apache 2.0
**Repo:** https://github.com/pbakaus/impeccable

**Что внутри:**
- Главный скилл `impeccable` с 7 reference-файлами (typography, color, spatial, motion, interaction, responsive, ux-writing)
- 18 команд: `/audit`, `/critique`, `/polish`, `/animate`, `/typeset`, `/layout`, `/colorize`, `/bolder`, `/quieter`, `/delight`, `/adapt`, `/harden`, `/distill`, `/clarify`, `/optimize`, `/overdrive`
- CLI-детектор антипаттернов: `npx impeccable detect src/`
- Встроенные anti-patterns (Inter ban, card nesting ban, bounce easing ban, gray-on-color ban)

**Когда использовать:**
- Доработка/полировка ЛЮБОГО фронтенда
- Как базовый дизайн-фреймворк для всех проектов

**Установка (глобально):**
```bash
git clone https://github.com/pbakaus/impeccable.git /tmp/impeccable
mkdir -p ~/.claude/skills
cp -r /tmp/impeccable/.agents/skills/* ~/.claude/skills/
rm -rf /tmp/impeccable
```

**Workflow:**
```
/impeccable teach     → собрать дизайн-контекст проекта
/audit                → технический аудит (a11y, perf, responsive)
/critique             → UX-ревью (hierarchy, clarity, resonance)
/typeset              → исправить шрифты
/layout               → исправить spacing
/animate              → добавить motion
/harden               → edge cases, error states
/polish               → финальная полировка
```

---

### 1.2 Taste Skill ⭐⭐⭐⭐⭐

**Назначение:** Набор стилевых скиллов с 3-dial параметризацией для генерации с нуля.
**Автор:** Leon Lin | **Stars:** 8.1k
**Repo:** https://github.com/Leonxlnx/taste-skill

**Что внутри (7 скиллов):**

| Скилл | Описание | Когда ставить |
|---|---|---|
| `taste-skill` | Основной: layout, typo, colors, spacing, motion. 3 диска | Всегда при генерации с нуля |
| `output-skill` | Anti-лень: запрещает `// rest of code`, placeholder'ы | Всегда рекомендую |
| `soft-skill` | Дорогой софтовый UI, spring-анимации, whitespace | Premium/luxury продукты |
| `minimalist-skill` | Notion/Linear стиль, монохром, crisp borders | Productivity tools |
| `redesign-skill` | Для рефакторинга существующего UI | Доработка чужих проектов |
| `brutalist-skill` | CRT + Swiss типографика (BETA) | Экспериментальные проекты |
| `stitch-skill` | Google Stitch совместимость | Если используешь Stitch |

**3 диска (только taste-skill):**

| Параметр | Что контролирует | Рекомендации по типу проекта |
|---|---|---|
| DESIGN_VARIANCE (1-10) | Экспериментальность layout | Landing=8, Dashboard=5, Chat=3, Admin=2 |
| MOTION_INTENSITY (1-10) | Количество анимаций | Landing=7, Dashboard=5, Chat=4, Admin=3 |
| VISUAL_DENSITY (1-10) | Плотность контента | Landing=3, Dashboard=7-8, Chat=5, Admin=9 |

**Ключевые ban-правила:** Inter, emoji, #000000, AI Purple, Unsplash, 3-card layout, h-screen, генерик-имена, слоп-копирайтинг.

**Установка (в проект):**
```bash
cd ~/project
git clone https://github.com/Leonxlnx/taste-skill.git /tmp/taste
mkdir -p .claude/skills
cp -r /tmp/taste/skills/taste-skill .claude/skills/
cp -r /tmp/taste/skills/output-skill .claude/skills/
# + опционально нужные стилевые скиллы
rm -rf /tmp/taste
```

**Настройка:** Открыть `.claude/skills/taste-skill/SKILL.md`, секция 1, выставить диски.
Или в чате: "Поставь DESIGN_VARIANCE=5, MOTION_INTENSITY=5, VISUAL_DENSITY=7"

---

### 1.3 Emil Kowalski Design Engineering ⭐⭐⭐⭐

**Назначение:** Философия design engineering от автора Sonner/Vaul (Linear, ex-Vercel).
**Автор:** Emil Kowalski (лично) | **Stars:** ~2k
**Repo:** https://github.com/emilkowalski/skill

**Ключевые принципы:**
- Frequency-based animation: чем чаще action → тем меньше анимации
- UI-анимации ≤ 300ms, лучше 180ms
- Press slow (2s linear), release fast (200ms ease-out)
- Spring physics: stiffness 300, damping 30
- clip-path как мощный animation primitive
- Good defaults > lots of options (из опыта Sonner: 13M+ weekly npm downloads)

**Когда использовать:** Рядом с impeccable `/animate` как reference для motion-философии. Особенно для productivity tools.

**Установка:**
```bash
git clone https://github.com/emilkowalski/skill.git /tmp/emil
cp -r /tmp/emil/skills/emil-design-eng ~/.claude/skills/
rm -rf /tmp/emil
```

---

### 1.4 Design Motion Principles ⭐⭐⭐⭐

**Назначение:** 3-perspective motion аудитор (Emil Kowalski × Jakub Krehel × Jhey Tompkins).
**Автор:** Kyle Zantos | **Stars:** 115
**Repo:** https://github.com/kylezantos/design-motion-principles

**Как работает:**
1. Context Reconnaissance → определяет тип проекта
2. Motion Gap Analysis → ищет conditional renders без AnimatePresence
3. Per-Designer Audit → оценка через 3 линзы:
   - **Emil** — сдержанность, скорость (productivity tools)
   - **Jakub** — production polish (consumer apps)
   - **Jhey** — playful experimentation (creative sites)

**8 reference-файлов:** emil-kowalski.md, jakub-krehel.md, jhey-tompkins.md, philosophy.md, technical-principles.md, accessibility.md, performance.md, common-mistakes.md

**Когда использовать:** Финальный аудит анимаций перед релизом.

**Установка:**
```bash
git clone https://github.com/kylezantos/design-motion-principles.git /tmp/dmp
cp -r /tmp/dmp/skills/design-motion-principles ~/.claude/skills/
rm -rf /tmp/dmp
```

---

## Категория 2: ENGINEERING WORKFLOW

Скиллы которые улучшают сам ПРОЦЕСС разработки: TDD, debugging, planning, code review.

### 2.1 Superpowers (obra) ⭐⭐⭐⭐⭐

**Назначение:** Полный workflow разработки: brainstorm → design → plan → TDD → subagents → review.
**Автор:** Jesse Vincent (Prime Radiant) | **Stars:** 94k+
**Repo:** https://github.com/obra/superpowers

**Это killer-скилл для любого серьёзного проекта.** Вот что он делает:

1. **brainstorming** — перед кодом уточняет что ты реально хочешь, показывает дизайн по частям
2. **using-git-worktrees** — изолирует фичу в отдельной worktree после утверждения дизайна
3. **test-driven-development** — жёсткий RED-GREEN-REFACTOR, код БЕЗ теста = удалить
4. **systematic-debugging** — 4-фазный root cause analysis (не random fixes)
5. **subagent-driven-development** — запускает субагентов на каждую задачу, ревьюит их работу
6. **code-review** — автоматический ревью против плана
7. **verification-before-completion** — нельзя сказать "готово" без доказательств

**Когда использовать:**
- Любой проект где важно качество кода
- Когда нужна автономная работа агента (часами без присмотра)
- НЕ для быстрого прототипирования (workflow тяжеловат для "just ship it")

**Установка:**
```bash
# Через plugin marketplace (рекомендуемый способ)
# В Claude Code:
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# Ручная:
git clone https://github.com/obra/superpowers.git /tmp/sp
cp -r /tmp/sp/.claude/skills/* ~/.claude/skills/
rm -rf /tmp/sp
```

**Основные команды:**
```
/superpowers:brainstorm      → начать мозгоштурм
/superpowers:write-plan      → написать план
/superpowers:execute-plan    → выполнить план субагентами
```

---

## Категория 3: BACKEND / PYTHON / API

Скиллы для серверной разработки. Экосистема тут слабее чем по фронту, но есть достойные варианты.

### 3.1 Jeffallan Claude Skills (66 skills) ⭐⭐⭐⭐⭐

**Назначение:** 66 специализированных скиллов для fullstack-разработки. Включает **FastAPI Expert**, **API Designer**, **Python Pro**, **Postgres Pro**, **Security Reviewer**, **Docker Engineer**, **Test Master** и ещё 59 скиллов.
**Автор:** Jeff Allan | **Stars:** ~1k
**Repo:** https://github.com/Jeffallan/claude-skills

**Что важно:** Скилл **FastAPI Expert** — один из лучших найденных. Он задаёт Claude персону senior Python-инженера с async SQLAlchemy, Pydantic V2, JWT/OAuth2, pytest-asyncio, dependency injection. Рядом стоят **API Designer** (OpenAPI 3.1, REST/GraphQL), **Postgres Pro**, **Security Reviewer**.

Скиллы автоматически комбинируются: промпт "Implement JWT auth in my FastAPI app" → активирует FastAPI Expert + Security Reviewer.

**Установка (выборочно, нужные скиллы):**
```bash
git clone https://github.com/Jeffallan/claude-skills.git /tmp/jskills

# FastAPI + API design + Python + Postgres + Security
mkdir -p ~/.claude/skills
cp -r /tmp/jskills/skills/fastapi-expert ~/.claude/skills/
cp -r /tmp/jskills/skills/api-designer ~/.claude/skills/
cp -r /tmp/jskills/skills/python-pro ~/.claude/skills/
cp -r /tmp/jskills/skills/postgres-pro ~/.claude/skills/
cp -r /tmp/jskills/skills/security-reviewer ~/.claude/skills/
cp -r /tmp/jskills/skills/docker-engineer ~/.claude/skills/
cp -r /tmp/jskills/skills/test-master ~/.claude/skills/

# Или ВСЕ 66 (но помни про лимит контекста):
# npx agent-skills-cli@latest add @Jeffallan/claude-skills

rm -rf /tmp/jskills
```

**Workflow комбинации из документации:**
```
FastAPI + Security Reviewer + Test Master   → безопасный API
API Designer + FastAPI Expert               → проектирование контракта → имплементация
Postgres Pro + FastAPI Expert               → оптимизация запросов
Docker Engineer + FastAPI Expert            → контейнеризация
```

---

### 3.2 Rafael Kamimura Claude Tools ⭐⭐⭐⭐

**Назначение:** Claude Code плагин заточенный под Python/FastAPI: скиллы, workflow-команды, hooks, 46 AI-агентов.
**Repo:** https://github.com/rafaelkamimura/claude-tools

**Ключевой скилл:** `fastapi-clean-architecture` — Clean Architecture + repository pattern для FastAPI. Автоматически активируется по триггерам: "fastapi", "clean architecture", "repository pattern", "build api", "create endpoint".

Также включает агентов: `backend-architect`, `code-architecture-reviewer`, `database-optimizer`, `performance-engineer`, `security-auditor`.

**Установка:**
```bash
# Через marketplace:
/plugin marketplace add rafaelkamimura/claude-tools
/plugin install claude-tools@claude-tools
```

---

### 3.3 Trail of Bits Modern Python ⭐⭐⭐⭐

**Назначение:** Modern Python tooling: uv, ruff, ty, pytest best practices.
**Автор:** Trail of Bits (одна из топовых security-компаний)
**Repo:** https://github.com/trailofbits/skills

Не про FastAPI конкретно, а про правильный Python в целом: линтинг, типизация, тестирование, toolchain. Хорошо сочетается с FastAPI Expert.

**Установка:**
```bash
git clone https://github.com/trailofbits/skills.git /tmp/tob
cp -r /tmp/tob/skills/modern-python ~/.claude/skills/
rm -rf /tmp/tob
```

---

### 3.4 CLAUDE.md Bible (FastAPI config) ⭐⭐⭐

**Назначение:** Не скилл, а набор из 25 stack-specific CLAUDE.md конфигов (80–150 строк каждый) для React, Next.js, FastAPI, Django, Svelte и т.д.
**Repo:** Часть awesome-claude-code-toolkit

**Зачем:** Это не skills, а CLAUDE.md файлы (проектные инструкции). FastAPI-конфиг задаёт паттерны и pitfalls конкретного стека. Хорошо сочетается с отдельными скиллами.

---

## Категория 4: SECURITY ⭐

### 4.1 VibeSec ⭐⭐⭐⭐⭐

**Назначение:** Security-first co-pilot. Учит Claude подходить к коду с позиции bug hunter'а.
**Автор:** BehiSecc | **Repo:** https://github.com/BehiSecc/VibeSec-Skill

**Что покрывает (60–70% типичных web-уязвимостей):**
- IDOR (Insecure Direct Object Reference) — проверка прав на каждый ресурс
- Privilege Escalation — серверная валидация ролей
- Horizontal Access — User A не может читать данные User B
- XSS, SQL Injection, SSRF
- Weak Authentication
- Access controls, security headers, input validation/sanitization

**Когда использовать:** На ЛЮБОМ web-проекте. Ставится глобально.
Цитата из awesome-lists: "If you use Claude to build web applications, do yourself a favor and use VibeSec-Skill to avoid getting hacked."

**Установка (глобально):**
```bash
git clone https://github.com/BehiSecc/VibeSec-Skill.git /tmp/vibesec
mkdir -p ~/.claude/skills/vibesec
cp /tmp/vibesec/SKILL.md ~/.claude/skills/vibesec/
rm -rf /tmp/vibesec
```

Триггеры: автоматически активируется на любом web-проекте или при "review security", "scan for vulnerabilities", "audit security".

---

### 4.2 OWASP Security ⭐⭐⭐⭐⭐

**Назначение:** OWASP Top 10:2025 + ASVS 5.0 + Agentic AI security (2026). Чеклисты для code review, secure patterns для 20+ языков.
**Автор:** agamm | **Repo:** https://github.com/agamm/claude-code-owasp

**Что внутри:**
- Security code review чеклисты: input handling, auth, access control, data protection, error handling
- Language-specific security quirks для 20+ языков (включая Python)
- ASVS 5.0 compliance checks

**Установка (одной командой):**
```bash
# В проект:
curl -sL https://raw.githubusercontent.com/agamm/claude-code-owasp/main/.claude/skills/owasp-security/SKILL.md \
  -o .claude/skills/owasp-security/SKILL.md --create-dirs

# Глобально:
curl -sL https://raw.githubusercontent.com/agamm/claude-code-owasp/main/.claude/skills/owasp-security/SKILL.md \
  -o ~/.claude/skills/owasp-security/SKILL.md --create-dirs
```

Триггеры: "Review this code for security issues", "Is this authentication implementation secure?"

---

### 4.3 Trail of Bits Security Skills ⭐⭐⭐⭐⭐

**Назначение:** Профессиональные security-скиллы от Trail of Bits — одной из лучших security-компаний в мире.
**Repo:** https://github.com/trailofbits/skills

**Что внутри (много отдельных скиллов):**
- `constant-time-analysis` — timing side-channels в crypto-коде
- `differential-review` — security-focused diff review с git history
- `insecure-defaults` — hardcoded secrets, default credentials, weak crypto
- `variant-analysis` — поиск похожих уязвимостей по паттернам
- `firebase-apk-scanner` — Firebase misconfigurations
- `modern-python` — современный Python tooling (uv, ruff, ty, pytest)

**Установка (выборочно):**
```bash
git clone https://github.com/trailofbits/skills.git /tmp/tob
# Выбери нужные:
cp -r /tmp/tob/skills/insecure-defaults ~/.claude/skills/
cp -r /tmp/tob/skills/differential-review ~/.claude/skills/
cp -r /tmp/tob/skills/modern-python ~/.claude/skills/
rm -rf /tmp/tob
```

---

### 4.4 Varlock ⭐⭐⭐⭐

**Назначение:** Управление env-переменными — гарантирует что секреты НИКОГДА не попадут в Claude-сессии, терминалы, логи или git.
**Repo:** В awesome-lists как `varlock-claude-skill`.

Особенно важно для проектов с API-ключами (Anthropic, WB/Ozon для Grafa, Asterisk для voice bot).

---

### 4.5 ClawSec (Prompt Security) ⭐⭐⭐

**Назначение:** Security suite с drift detection, automated audits, skill integrity verification.
**Автор:** Prompt Security | **Repo:** prompt-security/clawsec

Защищает от атак на сами скиллы (prompt injection через skills, supply chain атаки на SKILL.md).

---

## Категория 5: ТЕСТИРОВАНИЕ И ДЕБАГ

### 5.1 Systematic Debugging (из Superpowers) ⭐⭐⭐⭐⭐

4-фазный процесс: root-cause-tracing → defense-in-depth → condition-based-waiting → verification.
Включён в Superpowers, но можно ставить отдельно.
НЕ random fixes, а последовательный анализ.

### 5.2 Webapp Testing (Playwright) ⭐⭐⭐⭐

**Назначение:** Playwright automation для тестирования web-приложений прямо из Claude Code.
Claude может открыть браузер, кликать, проверять UI, делать скриншоты.

### 5.3 Test-Driven Development (из Superpowers) ⭐⭐⭐⭐⭐

Жёсткий TDD: RED → GREEN → REFACTOR, без исключений. Код без failing test = удалить.
Отдельно от Superpowers тоже работает как самостоятельный скилл.

### 5.4 Defense-in-Depth ⭐⭐⭐⭐

**Назначение:** Multi-layered testing и security best practices.
Дополняет TDD слоями: unit → integration → e2e → security → chaos.

---

## Категория 6: УТИЛИТЫ И DX

### 6.1 Claude API Skill (Official) ⭐⭐⭐⭐⭐

**Назначение:** Up-to-date API reference, SDK docs для 8 языков. Bundled с Claude Code.
**Repo:** https://github.com/anthropics/skills/tree/main/skills/claude-api

Полезно когда строишь что-то поверх Anthropic API (voice bot platform, RAG-системы).

### 6.2 Context7 (MCP) ⭐⭐⭐⭐

**Назначение:** Live documentation access — Claude Code подтягивает актуальную документацию любой библиотеки в контекст. MCP-сервер, не скилл.
Упоминается везде как must-have companion рядом со скиллами.

### 6.3 DuckDB Skills (Official) ⭐⭐⭐⭐

**Назначение:** SQL-запросы к файлам (CSV, JSON, Parquet, Excel), attach databases, search документации.
**Repo:** Официальные скиллы от DuckDB.

Скиллы: `attach-db`, `query`, `read-file`, `duckdb-docs`, `read-memories`, `install-duckdb`.

### 6.4 Changelog Generator ⭐⭐⭐

**Назначение:** User-facing changelog из git commits. Технические коммиты → customer-friendly release notes.

### 6.5 Everything Claude Code ⭐⭐⭐⭐

**Назначение:** Полная библиотека: 136 скиллов, 30 агентов, правила по стекам (Python, TypeScript, React, FastAPI...).
**Stars:** 128k | **Repo:** https://github.com/affaan-m/everything-claude-code

Включает rules для конкретных стеков:
```bash
cp -r everything-claude-code/rules/python ~/.claude/rules/
```

---

## Категория 6: ДОКУМЕНТЫ И ПРЕЗЕНТАЦИИ

Уже встроены в Claude.ai и Claude Code (Anthropic official):

| Скилл | Что делает |
|---|---|
| `docx` | Word документы (tracked changes, comments, formatting) |
| `pdf` | PDF: extract, merge, split, forms, OCR |
| `pptx` | PowerPoint: create, edit, layouts, templates |
| `xlsx` | Excel: formulas, charts, data transformations |

**Repo:** https://github.com/anthropics/skills (source-available, не open source)

Для КП в LaTeX — этих скиллов недостаточно, нужен кастомный.

---

## Категория 7: КАСТОМНЫЙ СКИЛЛ AXIOMATE

Создай свой скилл для специфики компании. Шаблон:

```bash
mkdir -p .claude/skills/axiomate/references
```

**`.claude/skills/axiomate/SKILL.md`:**
```markdown
---
name: axiomate-conventions
description: Axiomate Lab development conventions. Use alongside other skills
  for company-specific rules: stack, branding, API patterns, deployment.
---

# Axiomate Lab Conventions

## Stack
- Backend: FastAPI + PostgreSQL + SQLAlchemy
- Frontend: React + Vite + Tailwind
- Infra: Docker + Traefik on Nubes VMware (apps-prod-1)
- CI/CD: GitLab CI with private registry
- Auth: JWT tokens

## Branding
- Document fonts: Liberation Serif (headers), Inter (body)
- КП template: LaTeX tcolorbox
- [добавить: цвета, логотип usage]

## API Conventions
- REST, snake_case на всех endpoints
- Pydantic v2 для валидации
- Error format: {"detail": "...", "code": "..."}
- Pagination: limit/offset

## Frontend Conventions
- State: zustand для global, useState для local
- API client: axios через lib/api.ts
- Notifications: sonner
- Icons: Phosphor Icons
- Loading: skeleton loaders, не spinners

## File Structure
[описать структуру проекта]

## Deployment
- Multi-stage Docker build
- Traefik reverse proxy
- Environment: .env → VITE_API_URL
```

---

## Готовые сетапы по типу проекта

### Сетап A: Фронтенд с нуля (SaaS / dashboard)

```
ГЛОБАЛЬНЫЕ:
  ~/.claude/skills/impeccable/          ← дизайн-система
  ~/.claude/skills/animate/             ← /animate
  ~/.claude/skills/audit/               ← /audit
  ~/.claude/skills/polish/              ← /polish
  ~/.claude/skills/typeset/             ← /typeset
  ~/.claude/skills/layout/              ← /layout
  ~/.claude/skills/harden/              ← /harden

ЛОКАЛЬНЫЕ (.claude/skills/):
  taste-skill/          ← диски: VARIANCE=5, MOTION=5, DENSITY=7
  output-skill/         ← anti-лень
  axiomate/             ← ваши конвенции
```

### Сетап B: Доработка существующего фронта

```
ГЛОБАЛЬНЫЕ (Impeccable — уже стоит):
  все те же

ЛОКАЛЬНЫЕ:
  axiomate/             ← ваши конвенции
  # taste-skill НЕ нужен (он для генерации с нуля)
  # Используй команды: /audit → /critique → /typeset → /animate → /polish
```

### Сетап C: Fullstack проект (FastAPI + React)

```
ГЛОБАЛЬНЫЕ:
  impeccable/ + все команды     ← дизайн и UI workflow
  superpowers/                  ← TDD, debugging, planning, subagents
  vibesec/                      ← security на каждом web-проекте
  fastapi-expert/               ← FastAPI patterns, Pydantic V2, async
  api-designer/                 ← OpenAPI 3.1, REST/GraphQL контракты
  security-reviewer/            ← code review с фокусом на security

ЛОКАЛЬНЫЕ:
  taste-skill/                  ← для фронта (с нужными дисками)
  output-skill/                 ← anti-лень
  owasp-security/               ← если проект с auth/платежами
  axiomate/                     ← конвенции стека
```

### Сетап D: Быстрый прототип / MVP за день

```
ГЛОБАЛЬНЫЕ:
  impeccable/ + все команды

ЛОКАЛЬНЫЕ:
  taste-skill/           ← диски: VARIANCE=3, MOTION=3, DENSITY=5
  output-skill/
  # superpowers НЕ нужен (слишком тяжёлый workflow для прототипа)
  # Просто генерируй и потом /audit → /polish
```

### Сетап E: Landing page / маркетинг

```
ГЛОБАЛЬНЫЕ:
  impeccable/ + все команды

ЛОКАЛЬНЫЕ:
  taste-skill/           ← диски: VARIANCE=8, MOTION=7, DENSITY=3
  soft-skill/            ← или minimalist-skill (выбрать стиль)
  output-skill/
```

---

## Источники и каталоги для поиска новых скиллов

| Ресурс | Описание | URL |
|---|---|---|
| Anthropic Official | Официальные скиллы (docx, pdf, pptx, xlsx, claude-api) | https://github.com/anthropics/skills |
| awesome-claude-skills (travisvn) | Курируемый список, 22k+ stars | https://github.com/travisvn/awesome-claude-skills |
| awesome-agent-skills (VoltAgent) | 1000+ скиллов, community-maintained | https://github.com/VoltAgent/awesome-agent-skills |
| SkillsMP | Маркетплейс 800k+ скиллов | https://skillsmp.com |
| skills.sh | Поиск и превью скиллов | https://skills.sh |
| awesome-claude-code-toolkit | Полный toolkit: agents, skills, hooks, MCP | https://github.com/rohitg00/awesome-claude-code-toolkit |

---

## Настройка effort для работы со скиллами

Скиллы генерируют сложные многошаговые инструкции. Claude Code нужен reasoning.

```bash
# Навсегда — high effort (рекомендация)
claude config set -g effort high

# Или per-session через /model → стрелками выбрать effort level
```

| Effort | Когда | Токены |
|---|---|---|
| medium | Рутина, простые правки | Экономит |
| high | Работа со скиллами, сложные задачи | Баланс качества/стоимости |
| max | Архитектурные решения, сложный дебаг | Максимальный расход |

---

## Checklist перед началом работы

- [ ] Impeccable установлен глобально (`ls ~/.claude/skills/impeccable/`)
- [ ] VibeSec установлен глобально (`ls ~/.claude/skills/vibesec/`)
- [ ] Effort выставлен на high (`claude config set -g effort high`)
- [ ] Для FastAPI-проектов: fastapi-expert + api-designer + security-reviewer
- [ ] Для нового фронта: taste-skill + output-skill в `.claude/skills/`
- [ ] Диски taste-skill настроены под тип проекта
- [ ] Для серьёзного проекта: Superpowers установлен
- [ ] Для проектов с auth/платежами: OWASP Security установлен
- [ ] Кастомный axiomate скилл создан с конвенциями
- [ ] Первый запуск: `/impeccable teach` для сбора дизайн-контекста
