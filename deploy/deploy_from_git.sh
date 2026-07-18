#!/usr/bin/env bash
set -euo pipefail

APP="${COLONYMIND_APP_DIR:-/opt/openaidev}"
BRANCH="${COLONYMIND_BRANCH:-main}"
STAMP="$(date +%Y%m%d-%H%M%S)"

[[ "$APP" == /opt/* ]] || { echo "Refusing an unsafe application path" >&2; exit 1; }
[[ -d "$APP/.git" ]] || { echo "Expected a Git checkout at $APP" >&2; exit 1; }

cd "$APP"
mkdir -p backups
git fetch origin "$BRANCH"
TARGET="$(git rev-parse "origin/$BRANCH")"
CURRENT="$(git rev-parse HEAD)"

if [[ "$CURRENT" == "$TARGET" ]]; then
  echo "Already running $CURRENT"
  exit 0
fi

tar -czf "backups/openaidev-$STAMP-$CURRENT.tar.gz" --exclude=.git --exclude=backups .
git reset --hard "$TARGET"
docker compose up -d --build --remove-orphans

for attempt in {1..20}; do
  if curl -fsS "http://127.0.0.1:${COLONYMIND_PORT:-8200}/health" >/dev/null; then
    echo "Deployed $TARGET"
    exit 0
  fi
  sleep 2
done

echo "Health check failed; restoring $CURRENT" >&2
git reset --hard "$CURRENT"
docker compose up -d --build --remove-orphans
exit 1
