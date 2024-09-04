# FastAPI Template with asyncpg, Custom Migrations, and User Authentication using poetry

## Overview
This repository is a template for building high-performance web applications with FastAPI, leveraging `asyncpg` for asynchronous PostgreSQL interaction. It includes custom database migrations, user authentication with `bcrypt`, and follows best practices for scalable and secure Python web applications along with `poetry` for dependency management and black and flake8 for code formatting and linting.

## Features
- **FastAPI**: A modern, fast (high-performance), web framework for building APIs with Python 3.7+.
- **asyncpg**: An efficient, low-latency PostgreSQL database client library for Python.
- **Custom Migrations**: Manage your database schema with custom migration scripts.
- **User Authentication**: Basic authentication implemented using `bcrypt` for password hashing and verification.

## FAQ

- Want to use your own migration tool? Just remove `migrate.py` file from root and use your own migration tool.
- How does migrations work? Just add your SQL queries in `migrations` folder and run `python migrate.py` to apply them. make sure to include both -- up and -- down flags. 
#### Migration commands
- `python migrate.py --up` to apply all migrations.
- `python migrate.py --down` to rollback the last migration.
- `python migrate.py --down 1` to rollback the last 1 migration.
- `python migrate.py --specific filename` to apply a specific migration.