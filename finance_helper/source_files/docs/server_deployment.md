# Серверный запуск Finance Helper

Документ описывает актуальную схему запуска проекта на облачном сервере.

## 1. Общая схема

На сервере запускаются четыре процесса:

- `finance-service` на порту `8001`;
- `analytics-service` на порту `8002`;
- `api-gateway` на порту `8000`;
- `bot-service` как отдельный процесс Telegram-бота.

Mini App отдаётся через `api-gateway` и открывается по HTTPS-домену из переменной `MINIAPP_PUBLIC_URL`.

## 2. Подготовка окружения

```bash
cd finance_helper/source_files
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

После этого нужно заполнить `.env` реальными значениями. Файл `.env` нельзя публиковать в GitHub.

## 3. Миграции базы данных

```bash
cd finance_helper/source_files/services/finance-service
alembic upgrade head
```

## 4. Ручной запуск сервисов

```bash
# finance-service
cd finance_helper/source_files/services/finance-service
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

```bash
# analytics-service
cd finance_helper/source_files/services/analytics-service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

```bash
# api-gateway
cd finance_helper/source_files/services/api-gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
# bot-service
cd finance_helper/source_files/services/bot-service
python -m app.main
```

## 5. Проверка работоспособности

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8000/health
```

Mini App должна открываться по адресу вида:

```text
https://your-domain.example/miniapp/app
```

## 6. Важно для домена

Домен должен проксировать запросы к `api-gateway`. Для Mini App важны пути:

- `/miniapp/app`;
- `/miniapp/public/...`;
- API-запросы, которые Mini App отправляет через gateway.

