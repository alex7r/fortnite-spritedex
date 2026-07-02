#!/bin/sh
cd "$(dirname "$0")"
PORT="${1:-8765}"

if lsof -ti :"$PORT" >/dev/null 2>&1; then
  echo "Порт $PORT занят, освобождаю..."
  lsof -ti :"$PORT" | xargs kill -9 2>/dev/null
  sleep 0.5
fi

echo "Сервер: http://localhost:$PORT/tracker.html"
python3 -m http.server "$PORT"
