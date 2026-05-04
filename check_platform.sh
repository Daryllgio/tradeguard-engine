#!/usr/bin/env bash
set -e

echo "Checking C++ build..."
cmake -S cpp_engine -B build
cmake --build build

echo "Running C++ tests..."
./build/tradeguard_tests

echo "Generating sample data..."
python3 python_analytics/generate_sample_data.py

echo "Running engine..."
./build/tradeguard data/sample_ticks.csv output config/risk_config.json

echo "Running analytics..."
python3 python_analytics/report.py

echo "Compiling FastAPI files..."
python3 -m py_compile api/main.py api/brokers/*.py

echo "Building dashboard..."
cd dashboard
npm run build

echo "TradeGuard platform check passed."
