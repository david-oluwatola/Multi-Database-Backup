#!/usr/bin/env python3
import subprocess, hashlib, os, time, sqlite3
from datetime import datetime
from pathlib import Path
import os
import psycopg2
from psycopg2.extras import execute_values


metadata_pg_host = os.getenv("PGHOST", "localhost")
metadata_pg_dbname = os.getenv("METADATA_DB_NAME", "backup_metadata")
metadata_pg_user = os.getenv("METADATA_DB_USER", "postgres")
metadata_pg_password = os.getenv("METADATA_DB_PASSWORD", "postgrespass")

main_pg_host = os.getenv("POSTGRES_HOST", "localhost")
main_pg_dbname = os.getenv("POSTGRES_DB", "postgres")
main_pg_user = os.getenv("POSTGRES_USER", "postgres")
main_pg_password = os.getenv("POSTGRES_PASSWORD", "postgrespass")


BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "../backups"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
# METADB = BACKUP_DIR / "metadata.db"
# conn = sqlite3.connect(METADB)

conn = psycopg2.connect(
    host=metadata_pg_host,
    port=5432,
    dbname=metadata_pg_dbname,
    user=metadata_pg_user,
    password=metadata_pg_password
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS backups (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  db_type TEXT,
  file_path TEXT,
  checksum TEXT,
  size_bytes INTEGER,
  status TEXT,
  created_at TEXT,
  duration_seconds REAL,
  notes TEXT
)
""")
cur.execute("COMMIT")

def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def run_pg_dump():
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out = BACKUP_DIR / f"postgres-{timestamp}.dump"
    start = time.time()
    cmd = ["pg_dump", "-h", main_pg_host, "-p", "5432", "-U", main_pg_user, "-F", "c", "-b", "-v", "-f", str(out), main_pg_dbname]
    env = os.environ.copy()
    env["PGPASSWORD"] = main_pg_password
    try:
        subprocess.run(cmd, check=True, env=env)
        duration = time.time() - start
        checksum = sha256_of_file(out)
        size = out.stat().st_size
        cur.execute("""
            INSERT INTO backups(db_type, file_path, checksum, size_bytes, status, created_at, duration_seconds, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
            ("postgres", str(out), checksum, size, "OK", datetime.utcnow(), duration, None))
        cur.execute("COMMIT")

        print("Postgres backup OK:", out)
    except subprocess.CalledProcessError as e:
        cur.execute("""
            INSERT INTO backups(db_type, file_path, checksum, size_bytes, status, created_at, duration_seconds, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
            ("postgres", str(out), None, 0, "FAILED", datetime.utcnow(), 0.0, str(e)))
        cur.execute("COMMIT")
        raise

if __name__ == "__main__":
    run_pg_dump()

