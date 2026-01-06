#!/bin/sh
# Navigate to the directory where the code is stored
cd /app/bin
# Execute Python on the main script
exec python3 main.py "$@"
