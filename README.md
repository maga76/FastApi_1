# Internet Shop API

Экзаменационный проект на FastAPI, SQLAlchemy и SQLite.

## Запуск

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

База данных `internet_shop.db` создаётся автоматически.

## Структура

- `main.py` — endpoints;
- `models.py` — SQLAlchemy models;
- `schemas.py` — validation и response schemas;
- `crud.py` — CRUD и бизнес-логика;
- `database.py` — подключение к SQLite;
- `sqlite_database.py` — создание таблиц.
