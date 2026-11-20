#!/bin/bash
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 non trovato: installalo da https://www.python.org/downloads/"
  read -p "Premi Invio per chiudere"; exit 1
fi
python3 server.py 8080 desktop.html
