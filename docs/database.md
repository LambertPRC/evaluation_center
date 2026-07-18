# MySQL database-first workflow

The application maps every base table in the existing MySQL 5.7 database
`agent`. Views are inventoried but excluded from the generated writable ORM
models.

## Local configuration

Copy `.env.example` to `.env` and fill in the existing MySQL account:

```dotenv
DB_USER=your_existing_account
DB_PASSWORD=your_local_password
```

The password must remain in `.env`; never put it in source files, command-line
arguments, or Git. The same account is used by the application and the mapping
generator. It needs `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on `agent.*`,
but does not need DDL or administrative privileges.

Connection defaults are `127.0.0.1:3306`, database `agent`, and client charset
`utf8mb4`.

## Generate mappings

Run:

```powershell
uv run --locked python -m scripts.db_models generate
```

The command:

1. Connects with PyMySQL without putting credentials in process arguments.
2. Reflects every base table and excludes views.
3. Generates one SQLAlchemy 2 mapping module per table under
   `app/db/generated/`.
4. Runs Ruff, Pyright, mapper configuration, and table-set validation against
   the complete staged package.
5. Replaces the generated package only after all checks pass.

The generated package contains `base.py`, one `<table_name>.py` file per base
table, and aggregation modules. `models.py` remains as a compatibility import
surface but no longer contains table definitions. Importing
`app.db.generated` or `app.db.generated.models` loads every mapping so
cross-table relationships can be configured.

Do not edit files under `app/db/generated/` by hand. Repository queries,
business rules, and Pydantic API schemas belong in separate hand-written
modules.

## ORM repositories

Every generated model has a typed repository exported from `app.repositories`.
Each repository provides `create`, `get`, `list`, `update`, and `delete` async
methods. Scalar primary keys can be passed directly; use a mapping for composite
keys so the field names remain explicit:

```python
from datetime import date

from app.repositories import market_daily_bar_repository

async with session.begin():
    daily_bar = await market_daily_bar_repository.get(
        session,
        {"instrument_id": 1, "trade_date": date(2026, 7, 18)},
    )
```

Write methods flush but never commit or roll back. Services own the transaction
boundary, either with `session.begin()` or an explicit `commit()` / `rollback()`.
Repository create, update, and filter values accept mapped column names only;
primary keys cannot be changed by `update`.

## Check schema drift

Run:

```powershell
uv run --locked python -m scripts.db_models check
```

Use `--diff` when reviewed per-file model diffs are needed. Check mode never
replaces the committed generated package and returns a nonzero status when the
database schema, generated file set, or generated mappings differ.

Never run drift checks against an unreviewed production schema from ordinary
pull-request CI. Use a controlled integration database or schema-only copy.

## Runtime behavior

FastAPI creates one async SQLAlchemy engine per process when credentials are
configured. Each request receives its own `AsyncSession`; service code owns
commit and rollback boundaries.

- `GET /api/v1/health` checks only that the process is alive.
- `GET /api/v1/ready` verifies that MySQL is reachable with `SELECT 1`.

MySQL 5.7 does not enforce `CHECK` constraints. Range and state validation must
also be enforced by the Pydantic and service layers.
