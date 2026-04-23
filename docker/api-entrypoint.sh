#!/bin/sh
set -eu

mkdir -p /app/logs /app/data

if [ ! -f /app/.env ] && [ -f /app/.env.example ]; then
  cp /app/.env.example /app/.env
fi

exec "$@"
