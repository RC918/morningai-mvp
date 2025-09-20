#!/bin/bash
export PYTHONPATH=$(pwd)
python3 -m pytest --cov=src --cov-report=html --cov-report=term-missing

