#!/usr/bin/env python3
import subprocess, hashlib, os, time, sqlite3
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "../backups"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
METADB = BACKUP_DIR / "metadata.db"
conn = sqlite3.connect(METADB)
conn.execute("""
CREATE TABLE IF NOT EXISTS backups (
  id INTEGER PRIMARY KEY,
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
conn.commit()

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
    cmd = ["pg_dump", "-h", "localhost", "-p", "5432", "-U", "postgres", "-F", "c", "-b", "-v", "-f", str(out), "postgres"]
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "postgrespass")
    try:
        subprocess.run(cmd, check=True, env=env)
        duration = time.time() - start
        checksum = sha256_of_file(out)
        size = out.stat().st_size
        conn.execute("INSERT INTO backups(db_type,file_path,checksum,size_bytes,status,created_at,duration_seconds) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     ("postgres", str(out), checksum, size, "OK", datetime.utcnow().isoformat(), duration))
        conn.commit()
        print("Postgres backup OK:", out)
    except subprocess.CalledProcessError as e:
        conn.execute("INSERT INTO backups(db_type,file_path,checksum,size_bytes,status,created_at,duration_seconds,notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     ("postgres", str(out), None, 0, "FAILED", datetime.utcnow().isoformat(), 0.0, str(e)))
        conn.commit()
        raise

if __name__ == "__main__":
    run_pg_dump()

