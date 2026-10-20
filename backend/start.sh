#!/bin/sh
set -eu
python - <<'PY'
import time
from sqlalchemy import text
from app.db import engine
for attempt in range(30):
    try:
        with engine.connect() as c: c.execute(text('SELECT 1'))
        break
    except Exception:
        if attempt == 29: raise
        time.sleep(2)
PY
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-proxy-headers --no-access-log
