#!/bin/bash

echo "Running Só Golasso Tests..."
echo

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the tests
python run_tests.py

# Deactivate virtual environment
if [ -f "venv/bin/deactivate" ]; then
    deactivate
fi 