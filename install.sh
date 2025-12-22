#!/usr/bin/env bash
set -e

echo "Installing UDP Server Network Application..."

# Check docker
if ! command -v docker >/dev/null; then
  echo "Docker not found. Please install Docker first."
  exit 1
fi

docker compose up --build
