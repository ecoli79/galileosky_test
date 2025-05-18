# Galileosky_test

**Galileosky_test** — это REST API сервис, написанный с использованием FastAPI, предназначенный для работы с записями, хранящимися в базе данных PostgreSQL. Сервис предоставляет функциональность просмотра и перемещения записей в заданном порядке.

## 📦 Возможности

- Получение списка записей с пагинацией (`/records`)
- Перемещение записи между другими по `record_id` (`/records/move`)

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

## ⚙️ Установка и запуск

```bash
git clone https://github.com/your-username/Galileosky_test.git
cd Galileosky_test
docker compose up -d --build
```

После запуска сервис будет доступен по адресу:

```
http://localhost:8000
```

Остановка и удаление всех volume созданных при работе сервиса

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
GET http://localhost:8000/records?limit=3&offset=1
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

**Тело запроса:**

```json
{
  "record_id": 4,
  "before_id": 1,
  "after_id": 3
}
```

**Описание:**
Перемещает запись с `record_id = 4` между записями с `record_id = 1` и `record_id = 3`.

---

## 👤 Автор

Имполитов Денис  
📬 Email: [impol@mail.ru](mailto:impol@mail.ru)  
💬 Telegram: [@DenImpolitov](https://t.me/DenImpolitov)

## 📄 Лицензия

Этот проект лицензирован под лицензией MIT. Подробнее см. [LICENSE](./LICENSE).
