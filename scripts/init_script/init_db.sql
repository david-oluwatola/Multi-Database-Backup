
CREATE TABLE IF NOT EXISTS backups (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  db_type VARCHAR(50),
  file_path TEXT,
  checksum TEXT,
  size_bytes BIGINT,
  status VARCHAR(20),
  created_at TIMESTAMP,
  duration_seconds DOUBLE PRECISION,
  notes TEXT
);
