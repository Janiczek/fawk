#!/bin/bash
# FAWK Test Suite
# This script runs the comprehensive test suite with output validation

cd "$(dirname "$0")"

python3 run_tests.py
