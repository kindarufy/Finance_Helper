# Finance Helper

**Finance Helper** — микросервисный сервис для учёта и анализа личных финансов через Telegram-бота и Mini App.

Проект разработан как выпускная квалификационная работа и оформлен как полноценный backend case study: несколько FastAPI-сервисов, PostgreSQL, миграции, внутренний API, аналитика, совместные бюджеты, импорт банковских выписок, экспорт данных и автоматизированные тесты.

## Что демонстрирует проект

- проектирование backend-системы из нескольких сервисов;
- REST API на FastAPI;
- работу с PostgreSQL через SQLAlchemy и Alembic;
- Telegram Bot на aiogram;
- маршрутизацию запросов через API Gateway;
- внутреннюю аутентификацию сервисов по API-ключу;
- работу с пользовательскими и совместными бюджетами;
- аналитические отчёты и экспорт данных;
- Mini App как дополнительный пользовательский интерфейс;
- конфигурацию через переменные окружения;
- автоматизированные и ручные тестовые сценарии.

---

## Возможности

Пользователь может:

- вести учёт доходов и расходов;
- добавлять операции текстом, командами и кнопками меню;
- указывать дату операции, в том числе задним числом;
- просматривать, редактировать и удалять операции;
- создавать собственные категории доходов и расходов;
- назначать ключевые слова для автоматического подбора категории;
- устанавливать лимиты и бюджеты;
- получать предупреждения при достижении лимитов;
- формировать отчёты за период;
- получать дневную финансовую сводку;
- анализировать структуру расходов;
- использовать совместные бюджеты и рабочие пространства;
- экспортировать данные в CSV и XLSX;
- просматривать расширенную аналитику в Mini App;
- импортировать банковские выписки.

---

## Архитектура

```text
Telegram Bot                 Mini App
     │                           │
     └────────────┬──────────────┘
                  ▼
             API Gateway
              /       \
             /         \
            ▼           ▼
   Finance Service   Analytics Service
          ▲   │             │
          │   │             │ HTTP
          │   ▼             │
          │ PostgreSQL      │
          └─────────────────┘
```

`finance-service` является источником финансовых данных и работает с PostgreSQL. `analytics-service` запрашивает операции и лимиты у `finance-service` по внутреннему HTTP API, а не обращается к его базе напрямую.

### `finance-service`

Основной сервис данных. Отвечает за:

- пользователей;
- финансовые операции;
- категории;
- лимиты;
- рабочие пространства;
- участников совместных бюджетов;
- импорт банковских выписок.

### `analytics-service`

Сервис аналитики и отчётности:

- запрашивает финансовые данные у `finance-service`;
- формирует дневные сводки;
- строит отчёты за период;
- анализирует расходы;
- формирует экспорт CSV/XLSX;
- отдаёт данные для Mini App.

### `api-gateway`

Единая точка входа для пользовательских и внутренних запросов. Маршрутизирует запросы между сервисами и отдаёт Mini App.

### `bot-service`

Telegram-интерфейс на aiogram. Через бота доступны основные пользовательские сценарии Finance Helper.

### Mini App

Веб-интерфейс для расширенного просмотра финансовых данных и аналитики. В серверной конфигурации Mini App открывается по публичному HTTPS-адресу, указанному в `MINIAPP_PUBLIC_URL`.

Сервисы взаимодействуют по HTTP. Внутренние запросы защищены отдельным `INTERNAL_API_KEY`.

---

## Стек технологий

| Слой | Технологии |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Pydantic |
| Telegram | aiogram, Telegram Bot API |
| Database | PostgreSQL, SQLAlchemy |
| Migrations | Alembic |
| API | REST, internal service-to-service HTTP |
| Mini App | HTML, CSS, JavaScript, Telegram Mini App |
| Testing | pytest, ручные test scenarios |
| Deployment | облачный сервер, HTTPS-домен, отдельные Python-процессы |

В актуальной серверной конфигурации проекта Docker и `ngrok` не требуются.

---

## Структура проекта

```text
Finance_Helper/
├── README.md
└── finance_helper/
    ├── run_and_configuration_guide/
    │   └── Finance_Helper_Guide.pdf
    └── source_files/
        ├── .env.example
        ├── Makefile
        ├── pytest.ini
        ├── requirements.txt
        ├── docs/
        │   └── test_scenarios.md
        ├── scripts/
        │   └── seed_demo.py
        ├── services/
        │   ├── analytics-service/
        │   ├── api-gateway/
        │   ├── bot-service/
        │   └── finance-service/
        └── tests/
```

Рабочая директория:

```text
finance_helper/source_files
```

---

## Настройка окружения

Перейдите в рабочую директорию и создайте `.env` из безопасного шаблона:

```bash
cd finance_helper/source_files
cp .env.example .env
```

Основные переменные:

| Переменная | Назначение |
| --- | --- |
| `BOT_TOKEN` | токен Telegram-бота |
| `INTERNAL_API_KEY` | ключ внутренних запросов между сервисами |
| `MINIAPP_SIGNING_SECRET` | секрет для подписи Mini App token/data |
| `MINIAPP_PUBLIC_URL` | публичный HTTPS-адрес Mini App |
| `FINANCE_URL` | адрес finance-service |
| `ANALYTICS_URL` | адрес analytics-service |
| `GATEWAY_URL` | адрес API Gateway |
| PostgreSQL variables | параметры подключения к базе данных |

> Реальный `.env` не должен попадать в GitHub. В репозитории хранится только `.env.example` без рабочих секретов.

---

## Установка

```bash
cd finance_helper/source_files
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

На Windows активируйте окружение командой:

```powershell
.\venv\Scripts\Activate.ps1
```

## Миграции базы данных

После создания PostgreSQL database выполните:

```bash
cd finance_helper/source_files/services/finance-service
alembic upgrade head
```

---

## Запуск сервисов

### Finance Service

```bash
cd finance_helper/source_files/services/finance-service
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Analytics Service

```bash
cd finance_helper/source_files/services/analytics-service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### API Gateway

```bash
cd finance_helper/source_files/services/api-gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Telegram Bot

```bash
cd finance_helper/source_files/services/bot-service
python -m app.main
```

Для постоянного серверного запуска процессы можно оформить как `systemd` services или использовать другой process manager.

---

## Mini App

В `.env` задаётся публичный HTTPS URL:

```env
MINIAPP_PUBLIC_URL=https://your-domain.example/miniapp/app
```

Маршруты `/miniapp/app` и `/miniapp/public/...` должны направляться в `api-gateway`.

---

## Demo seed

Для заполнения системы демонстрационными данными:

```bash
cd finance_helper/source_files
python scripts/seed_demo.py
```

Скрипт использует `GATEWAY_URL`, `INTERNAL_API_KEY`, `DEMO_TELEGRAM_ID` и `DEMO_TELEGRAM_USERNAME`.

---

## Тестирование

Автоматизированные тесты находятся в:

```text
finance_helper/source_files/tests
```

Запуск:

```bash
cd finance_helper/source_files
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Часть smoke-тестов проверяет работающий `api-gateway`. Если gateway не запущен, соответствующие integration checks могут быть пропущены.

Ручные сценарии находятся в:

```text
finance_helper/source_files/docs/test_scenarios.md
```

---

## Документация

- `README.md` — обзор проекта и быстрый запуск;
- `finance_helper/run_and_configuration_guide/Finance_Helper_Guide.pdf` — подробное руководство по конфигурации;
- `finance_helper/source_files/docs/test_scenarios.md` — ручные тестовые сценарии.

---

## Статус

Проект завершён как релизная версия ВКР и подготовлен к запуску на облачном сервере.

Репозиторий используется как portfolio case по **Python backend, FastAPI, микросервисной архитектуре, PostgreSQL, Telegram integrations и тестированию**.

## Автор

[Николь Журбенко](https://github.com/nikamurkaa)
