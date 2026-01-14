#!/bin/bash
export PYTHONPATH=/app/bin
exec python3 /app/bin/main.py "$@"
