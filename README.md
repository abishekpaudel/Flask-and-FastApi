# Marine Parts Inventory API (Flask + FastAPI + MySQL + Docker)

A small learning project for practising Python REST APIs, SQL, and Docker. It contains two implementations of the same API:
- Flask: `http://localhost:8001`
- FastAPI: `http://localhost:8002` (interactive docs at `/docs`)

Both APIs connect to the same MySQL database when started with Docker Compose.

> **Learning/demo project:** the credentials in `docker-compose.yml` are local-development credentials only. Do not use them in production. This project is intentionally small and does not implement authentication, authorization, migrations, or production-grade logging.

## 1. Architecture and request flow

```text
Client (curl / Postman / frontend)
          |
          | HTTP request + JSON
          v
   Flask API :8001     FastAPI API :8002
          |                    |
          +---------+----------+
                    |
                    | common/db.py
                    v
              MySQL database
              database: marine_parts
              table: parts
```

For a request such as `POST /parts`:
1. The client sends JSON to the API.
2. Flask manually validates the JSON, or FastAPI validates the body using a Pydantic model.
3. The route calls a function in `common/db.py`.
4. The database helper opens a MySQL connection and runs a parameterized SQL statement.
5. MySQL enforces constraints such as the unique SKU.
6. The API turns the result into JSON and returns an HTTP status code.

## 2. Requirements

- Docker Desktop / Docker Engine with the Compose plugin.
- Or, for local development: Python 3.12+ and a reachable MySQL 8 server.

## 3. Run the complete project with Docker

From this folder:

```bash
docker compose up --build
```

Wait until the MySQL health check succeeds and the API containers start.

- Flask: <http://localhost:8001/parts>
- FastAPI: <http://localhost:8002/parts>
- FastAPI Swagger UI: <http://localhost:8002/docs>

Stop the services with `Ctrl+C`; remove the containers with:

```bash
docker compose down
```

To also delete the persisted local database volume and all data inside it:

```bash
docker compose down -v
```

## 4. Try the API

The examples below use FastAPI. Replace `8002` with `8001` to try Flask.

### Create a part — `POST /parts`

```bash
curl -i -X POST http://localhost:8002/parts \
  -H "Content-Type: application/json" \
  -d '{"name":"Marine Pump","sku":"PUMP-001","quantity":10,"price":249.99}'
```

Expected: `201 Created`.

### List parts — `GET /parts`

```bash
curl -i http://localhost:8002/parts
```

Expected: `200 OK`.

### Get one part — `GET /parts/1`

```bash
curl -i http://localhost:8002/parts/1
```

Expected: `200 OK`, or `404 Not Found` if that ID does not exist.

### Replace a part — `PUT /parts/1`

```bash
curl -i -X PUT http://localhost:8002/parts/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Marine Pump V2","sku":"PUMP-001","quantity":8,"price":259.99}'
```

Expected: `200 OK`, or `404 Not Found`.

### Delete a part — `DELETE /parts/1`

```bash
curl -i -X DELETE http://localhost:8002/parts/1
```

Expected: `204 No Content`, or `404 Not Found`.

### Try invalid data

```bash
curl -i -X POST http://localhost:8002/parts \
  -H "Content-Type: application/json" \
  -d '{"name":"","sku":"PUMP-002","quantity":-1,"price":10}'
```

FastAPI returns `422` for Pydantic validation errors. Flask uses manual validation and returns `400` for invalid input. Both APIs return `409` when the SKU conflicts with an existing record.

## 5. Endpoints

| Method | Endpoint | Purpose | Typical success |
|---|---|---|---|
| GET | `/parts` | List parts | 200 |
| GET | `/parts/{id}` | Get one part | 200 |
| POST | `/parts` | Create a part | 201 |
| PUT | `/parts/{id}` | Replace part fields | 200 |
| DELETE | `/parts/{id}` | Delete a part | 204 |

Part JSON:

```json
{
  "name": "Marine Pump",
  "sku": "PUMP-001",
  "quantity": 10,
  "price": 249.99
}
```

## 6. Files explained

- `common/db.py`: MySQL connection settings, table creation, and SQL CRUD functions shared by both APIs.
- `flask_app/app.py`: Flask routes and manual request validation.
- `fastapi_app/main.py`: FastAPI routes, Pydantic validation, and automatic API docs.
- `requirements-*.txt`: dependencies for each framework.
- `Dockerfile.*`: instructions to package each API in its own image.
- `docker-compose.yml`: starts MySQL and both APIs together, and waits for MySQL health.
- `.dockerignore`: excludes local files from Docker build context.

## 7. Map this to Express.js

| Familiar Express concept | Flask | FastAPI |
|---|---|---|
| `express()` app | `Flask(__name__)` | `FastAPI()` |
| `app.get('/parts', handler)` | `@app.get('/parts')` | `@app.get('/parts')` |
| `req.body` | `request.get_json()` | typed function parameter such as `data: PartInput` |
| `res.status(201).json(data)` | `return jsonify(data), 201` | return data and configure `status_code=201` |
| Middleware / validation library | manual checks or extensions | Pydantic model validation and dependencies |
| DB module / repository | `common/db.py` | `common/db.py` |

The framework changes, but the core backend concepts are the same: HTTP, input validation, business rules, SQL, error handling, and response codes.

## 8. SQL concepts demonstrated

- Primary key: `id`
- Unique constraint: `sku`
- `NOT NULL`: required fields
- `CHECK`: quantity and price cannot be negative
- Parameterized queries: `%s` placeholders prevent user values from being interpreted as SQL syntax
- Connections are opened for each operation and closed in a `finally` block

## 9. Docker concepts demonstrated

- **Image:** packaged application blueprint.
- **Container:** running instance of an image.
- **Dockerfile:** instructions to build an image.
- **Port mapping:** host ports 8001/8002 map to container port 8000.
- **Environment variables:** configure database connection without hardcoding settings in Python.
- **Named volume:** `mysql_data` keeps MySQL data when containers are removed.
- **Health check:** Compose waits for MySQL to be ready before starting the APIs.


## 11. Local run without Docker (optional)

Install and run one framework at a time from the project root. First start a local MySQL server and create a database/user matching your environment, then set environment variables.

Example for macOS/Linux:

```bash
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=marine_app
export DB_PASSWORD=change_me
export DB_NAME=marine_parts
```

Install Flask dependencies and run:

```bash
pip install -r requirements-flask.txt
python -m flask_app.app
```

For FastAPI, stop Flask and run:

```bash
pip install -r requirements-fastapi.txt
uvicorn fastapi_app.main:app --reload --port 8000
```

If your local MySQL credentials differ, adjust the environment variables. Never commit real credentials.

## 12. Automated tests with pytest

The project includes tests for both Flask and FastAPI in `tests/`. These are API-level unit tests: they exercise the route and validation behavior, while replacing the database functions with test doubles. **They do not require a running MySQL server and do not verify real SQL queries.**

Install the test dependencies in a virtual environment:

```bash
pip install -r requirements-test.txt
```

Run all tests from the project root:

```bash
python -m pytest -v
```

Run only one framework's tests:

```bash
python -m pytest tests/test_flask_api.py -v
python -m pytest tests/test_fastapi_api.py -v
```

A passing test looks like `PASSED`; a failure shows which assertion failed and the traceback. The tests cover successful list/create/delete requests, invalid input, and missing IDs.

### How the tests work

- `client.get(...)` / `client.post(...)` sends a simulated HTTP request to the app without starting a real web server.
- `assert response.status_code == 201` checks the expected HTTP status.
- `monkeypatch` replaces database functions with predictable in-memory responses, so tests are fast and independent of MySQL.
- Flask uses `app.test_client()`.
- FastAPI uses `fastapi.testclient.TestClient`, backed by `httpx`.

### Unit test vs integration test

- **Unit/API route test (included):** checks route behavior with the database layer replaced.
- **Integration test (next step):** starts a real MySQL test database and verifies actual inserts, reads, constraints, and cleanup.
- **End-to-end test:** runs the whole deployed stack and sends requests through the exposed API.

For a short internship interview, be ready to explain what is being tested, why the database is mocked, and what additional confidence an integration test against MySQL would provide.

## 13. Next improvements

1. Add automated tests with `pytest` and a test database.
2. Add `PATCH` for partial updates.
3. Add pagination and search by SKU/name.
4. Add authentication and authorization.
5. Use SQLAlchemy/Alembic for ORM and schema migrations.
6. Add structured logging and consistent error responses.
