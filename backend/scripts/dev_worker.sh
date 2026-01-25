#!/bin/sh
set -eu

while true; do
  PYTHONPATH=. python -m celery -A app.workers.celery_app:celery_app worker --loglevel=info &
  worker_pid=$!

  python - <<'PY'
import os
import time


def snapshot() -> float:
    latest = 0.0
    for root, _, files in os.walk("app"):
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            try:
                latest = max(latest, os.path.getmtime(path))
            except FileNotFoundError:
                continue
    return latest


last = snapshot()
while True:
    time.sleep(1)
    current = snapshot()
    if current != last:
        print("Detected code change. Restarting worker.")
        break
PY

  kill "${worker_pid}" || true
  wait "${worker_pid}" || true
done
