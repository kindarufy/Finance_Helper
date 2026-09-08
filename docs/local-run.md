# Локальный запуск Finance Helper

Используйте Python 3.11 и PostgreSQL 14+ с отдельной локальной базой.
Telegram-бот, домен и HTTPS для демонстрации в браузере не нужны.

1. Из корня репозитория перейдите в `finance_helper/source_files`.
2. Создайте окружение: `python -m venv venv`.
3. Активируйте его: `source venv/bin/activate` (Linux/macOS) или
   `.\venv\Scripts\Activate.ps1` (PowerShell).
4. Установите зависимости: `python -m pip install -r requirements.txt`.
5. Скопируйте `.env.example` в `.env`.
6. Создайте в PostgreSQL отдельную роль и базу. Например, из psql под администратором:

```sql
CREATE USER finance_local WITH PASSWORD 'replace-with-a-local-password';
CREATE DATABASE finance_local OWNER finance_local;
```

Укажите соответствующие POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
POSTGRES_USER и POSTGRES_PASSWORD в .env. Секреты не публикуйте.

Из `finance_helper/source_files`:

```bash
python scripts/run_demo.py
```

Launcher применяет миграции, запускает три сервиса на 127.0.0.1:8100–8102
и выводит временную ссылку Mini App. Откройте её в браузере.
Ссылка содержит токен: не публикуйте её. Данные остаются в выбранной БД.
Остановка всех трёх сервисов — Ctrl+C в том же терминале.

Если порты заняты: `python scripts/run_demo.py --port 8200`.
Проверка с автоматической остановкой: `python scripts/run_demo.py --smoke-test`.

## Тесты

В активированном окружении, из source_files:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q
```

Часть интеграционных тестов требует работающего gateway.
PDF-руководство описывает отдельный серверный сценарий. Этот файл описывает
локальную демонстрацию и дополняет его.
