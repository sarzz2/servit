<div>

[![Licence](https://img.shields.io/badge/licence-MIT-blue.svg)](/LICENSE)

</div>

# Servit

This project is a backend service built with FastAPI and uses PostgreSQL as its database. It supports various features like user management, server management, friend system, and chat messaging, with integrated permissions and role management. The project implements coverage tests, linting, and code formatting through CI/CD pipelines with GitHub Actions.


## Requirements

- Python 3.12+
- PostgreSQL
- Poetry (for dependency management)
- Redis (if applicable for caching)

## Setup

You can set up this project by installing all the dependencies and running the server locally or using Docker.
To run using docker, you can use the following commands:

```bash
docker compose up --build
```
As simple as that.

To run the project locally, follow the steps below:

### 1. Clone the Repository

```bash
git clone https://github.com/{yourusername}/servit.git
cd servit
```
### 2. Install the dependencies

```bash
poetry install
```

### 3. Create a `.env` file in the root directory and add the following environment variables(check .env.example for full variable list):



### 4. Apply the database migrations

```bash
python migrate.py
```

All migration commands:-
- `python migrate.py --up` to apply all migrations.
- `python migrate.py --down` to rollback the last migration.
- `python migrate.py --down 1` to rollback the last 1 migration.
- `python migrate.py --specific filename` to apply a specific migration.

### 5. Set up pre-commit hooks
```
poetry run pre-commit install
```
This will run the checks defined in `.pre-commit-config.yaml` before every commit to ensure that the code is properly formatted and linted.

To run precommit before commiting
```bash
precommit
```
### 6. Run the server

```bash
uvicorn app.main:app --reload
```
or
```bash
fastapi run dev
```

### 7. Open the browser and go to `http://localhost:8000/docs` to view the API documentation.


## Background Worker

This project is using celery with RabbitMQ to run background tasks.


To run celery beat & worker :-
```bash
 celery -A app.celery_app.celery_app worker --loglevel=debug
```

```bash
 celery -A app.celery_app.celery_app worker --loglevel=debug
```

## Testing
You can run tests using pytest:

```bash
poetry run pytest --cov=./
```

## Formatting and Linting
You can run the following commands to format and lint the code:

```bash
poetry run isort .
poetry run black .
poetry run flake8
```

## Monitoring
You can monitor the application using the following tools:
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
