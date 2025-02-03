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

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/db_name
TEST_DATABASE_URL=postgresql://user:password@localhost/test_db_name # required to run tests locally
S3_ENDPOINT_URL=http://localhost:4566 # for localstack
S3_REGION_NAME=us-east-1
```

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
5. Run the server

```bash
uvicorn app.main:app --reload
```
or
```bash
fastapi run dev
```

### 6. Open the browser and go to `http://localhost:8000/docs` to view the API documentation.

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
