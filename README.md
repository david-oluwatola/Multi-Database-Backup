### Multi-DB Backup

A minimal, containerized toolkit to perform automated database backups (starting with Postgres), store artifacts on disk, and track backup metadata in a lightweight SQLite catalog. Includes optional Metabase for quick visibility into backup history.

---

## Features
- **Postgres backups** using `pg_dump` with custom format (`-F c`).
- **Checksum + size** recorded for each backup file.
- **SQLite metadata catalog** stored alongside backups in `backups/metadata.db`.
- **Dockerized runtime** via `docker-compose` for Postgres, MySQL (placeholder), Metabase, and a backup runner.
- **Extensible**: add more databases (e.g., MySQL, Oracle) by adding new scripts and wiring them in `docker-compose.yml`.

---

## Project Structure
- `scripts/backup_postgres.py`: Runs a Postgres backup and writes a record to `backups/metadata.db`.
- `backups/`: Backup artifacts and the SQLite metadata catalog live here.
- `docker-compose.yml`: Services for Postgres, MySQL, Metabase, and the backup runner.
- `Dockerfile`: Image used by `backup-runner` service.
- `requirements.txt`: Python dependencies for the runner image (if any).

---

## Prerequisites
- Docker and Docker Compose installed.
- macOS/Linux or Windows with WSL2.

---

## Quick Start
1. Optional: create a `.env` file in the project root to override defaults.
2. Start the stack:

```bash
docker compose up -d --build
```

This will:
- Start `postgres:15` bound to `localhost:5432`.
- Start `mysql:8.0` bound to `localhost:3306` (currently a placeholder for future backups).
- Start `metabase` at `http://localhost:3000`.
- Build and run `backup-runner` which executes `scripts/backup_postgres.py` once on container start.

Backup files will appear under `backups/` named like `postgres-YYYYMMDD-HHMMSS.dump`. A corresponding record is written to `backups/metadata.db`.

---

## Environment Variables
You can set these via shell exports, a `.env` file at the repo root, or directly in `docker-compose.yml`.

- `POSTGRES_PASSWORD` (default: `postgrespass`)
- `MYSQL_ROOT_PASSWORD` (default: `mysqlpass`)
- `PGHOST` (default: `localhost`) – host that `pg_dump` connects to
- `BACKUP_DIR` (default inside runner: `/app/backups`; host-mounted to `./backups`)

Example `.env`:

```bash
POSTGRES_PASSWORD=supersecret
MYSQL_ROOT_PASSWORD=anothersecret
PGHOST=postgres
```

When using Docker, `PGHOST=postgres` ensures the runner connects to the Postgres service on the Docker network.

---

## How Backups Work (Postgres)
`scripts/backup_postgres.py`:
- Ensures `BACKUP_DIR` exists.
- Runs `pg_dump -h $PGHOST -p 5432 -U postgres -F c -b -v -f <file> postgres`.
- Uses `PGPASSWORD=$POSTGRES_PASSWORD` for auth.
- Computes SHA-256, file size, duration, and writes a row to SQLite table `backups` with fields:
  - `db_type`, `file_path`, `checksum`, `size_bytes`, `status`, `created_at`, `duration_seconds`, `notes`.

On success, `status` is `OK`. On failure, a `FAILED` row is inserted with the error message in `notes`.

---

## Running Manually (without Docker)
Ensure `pg_dump` and Python 3 are available, and that Postgres is reachable on `localhost:5432` or adjust `PGHOST`.

```bash
python3 scripts/backup_postgres.py
```

Artifacts and `metadata.db` will be created under `backups/` in the repo by default.

---

## Viewing Backup History in Metabase
Metabase is available at `http://localhost:3000`.

The included Metabase service is configured to use the Postgres service for its own application DB. To analyze the backup catalog (`backups/metadata.db`), add a new SQLite database in Metabase and point it at the file on the host, or expose it via another service. Simpler local option: open the SQLite database using a desktop client (e.g., DB Browser for SQLite) and query the `backups` table.

---

## Restoring a Postgres Backup
Given a file like `backups/postgres-YYYYMMDD-HHMMSS.dump` created with custom format:

```bash
# Restore into a new database named mydb
createdb -h localhost -U postgres mydb
pg_restore -h localhost -U postgres -d mydb -v backups/postgres-YYYYMMDD-HHMMSS.dump
```

If using Docker, you can exec into the Postgres container or map tools from your host. Ensure `PGPASSWORD` is set.

---

## Extending to Other Databases
To add another database type (e.g., MySQL):
1. Create a new script under `scripts/` (e.g., `backup_mysql.py`) that writes to the same SQLite schema.
2. Add environment needed (e.g., `MYSQL_ROOT_PASSWORD`).
3. Update `docker-compose.yml` to run your script via the `backup-runner` or a new service.

The `backups` table is generic so multiple DB types can co-exist.

---

## Troubleshooting
- Backup file not created: check runner logs `docker compose logs backup-runner`.
- Auth failures: ensure `POSTGRES_PASSWORD` matches the Postgres container. With Docker, prefer `PGHOST=postgres`.
- `pg_dump` not found (bare-metal run): install Postgres client tools.
- SQLite locked errors: avoid running multiple backup writers concurrently to the same `metadata.db` without coordination.

---

## License
MIT. See `LICENSE` if present, or adapt as needed.


