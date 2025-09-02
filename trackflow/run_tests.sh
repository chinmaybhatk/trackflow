#!/bin/bash
# Run TrackFlow tests locally

echo "Running TrackFlow End-to-End Tests..."

# Backend tests
echo "1. Running backend tests..."
bench --site test_site run-tests --app trackflow --module trackflow.tests.test_trackflow_e2e

# API tests  
echo "2. Running API tests..."
bench --site test_site execute trackflow.tests.test_api

# For UI tests (requires Playwright)
if command -v playwright &> /dev/null; then
    echo "3. Running UI tests..."
    pytest apps/trackflow/trackflow/tests/test_ui.py -v
else
    echo "Playwright not installed. Run: pip install playwright && playwright install"
fi

echo "Test run complete!"
