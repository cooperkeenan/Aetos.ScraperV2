#!/bin/bash

echo "Activating Virtual Environment"
echo ""


if [ -d ".venv" ]; then
   echo "venv found"
   source .venv/bin/activate
   pip install -r requirements.txt
else
   echo "No venv found, creating new one..."
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
fi

echo "Running Startup Command"
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload