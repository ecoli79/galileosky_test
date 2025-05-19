# Galileosky_test

**Galileosky_test** — это REST API сервис, написанный с использованием FastAPI, предназначенный для работы с записями, хранящимися в базе данных PostgreSQL. Сервис предоставляет функциональность просмотра и перемещения записей в заданном порядке.

## 📦 Возможности

- Получение списка записей с пагинацией (`/records`)
- Перемещение записей (`/records/move`)

Пример записей, хранящихся в БД:
```json
[
  {"id": 1, "sort_order": 1000, "record_name": "Record 1"},
  {"id": 2, "sort_order": 2000, "record_name": "Record 2"},
  {"id": 3, "sort_order": 3000, "record_name": "Record 3"},
  {"id": 4, "sort_order": 4000, "record_name": "Record 4"},
  {"id": 5, "sort_order": 5000, "record_name": "Record 5"}
]
```

## 🚀 Технологии

- Python 3.12
- FastAPI
- Docker Compose
- PostgreSQL

## 📦 Структура проект
- директория /app/ основная директория проекта.
- директория /app/migrations/ файлы миграции для базы данных
- директория /app/scripts/ python скрипты для исполнения миграций базы данных.
- директория /test/ тесты для проверки рабочих модулей сервиса

## ⚙️ Установка и запуск
Внимание! При первом запуске сервис заполняет базу данных 100 млн. строк, размер базы примерно 7.5 Gb. 
Если вы не хотите заполнять базу данных можно закомментировать одну строку в файле /app/scripts/migrate.py. Нужно закомментировать строку в процедуре main() generate_data()
```python
def main():
    ensure_migrations_table()
    applied = get_applied_migrations()

    files = sorted(f for f in os.listdir(MIGRATION_DIR) if f.endswith('.sql'))

    for filename in files:
        version = filename
        if version in applied:
            print(f'Skipping already applied migration {version}')
            continue
        
        filepath = os.path.join(MIGRATION_DIR, filename)
        sql = parse_migration_file(filepath)
        apply_migration(version, sql)
        
    # for populate data in table records
    generate_data()
```

Запуск сервиса:
```bash
git clone https://github.com/your-username/Galileosky_test.git
cd Galileosky_test
docker compose up -d --build
```

После запуска сервис будет доступен по адресу:

```
http://localhost:8000
```

Остановка и удаление всех volumes созданных при работе сервиса

```
docker compose down -v
```

Для запуска тестов необходимо установить зависимости из директории /test/requirements.txt
После этого запускаем тесты:

```
$pytest -v
```


## 📘 Использование API

### Получить список записей

`GET /records`

**Параметры запроса (необязательные):**
- `limit` — количество записей (по умолчанию: 100)
- `offset` — смещение (по умолчанию: 0)

📥 **Пример запроса:**

```
GET http://ip_host:8000/records?limit=3&offset=1
```

📤 **Пример ответа:**

```json
[
  {"id": 2, "sort_order": 2000, "record_name": "Record 2"},
  {"id": 3, "sort_order": 3000, "record_name": "Record 3"},
  {"id": 4, "sort_order": 4000, "record_name": "Record 4"}
]
```
---

### Переместить запись

`POST /records/move`

```
curl -X POST http://ip_host/records/move -H "Content-Type: application/json"  -d '{"record_id": 4, "before_id": 1, "after_id": 3}'
```

**Тело запроса:**

```json
{
  "record_id": 4,
  "before_id": 1,
  "after_id": 3
}
```

📤 **Пример ответа:**

```
json {"id":4,"sort_order":2500,"record_name":"a87ff679a2f3"}
```
Метода возвращает данные записи с измененным полем sort_order


**Описание:**
Перемещает запись с `record_id = 4` между записями с `record_id = 1` и `record_id = 3`.

---

## 👤 Автор

Имполитов Денис  
📬 Email: [impol@yandex.ru](mailto:impol@yandex.ru)  
💬 Telegram: [@DenImpolitov](https://t.me/DenImpolitov)

## 📄 Лицензия

Этот проект лицензирован под лицензией MIT. Подробнее см. [LICENSE](./LICENSE).
