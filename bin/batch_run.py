#!/usr/bin/env python3
import sys
import os

# command/ を PYTHONPATH に追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from job_framework.batch_run import BatchRunnerJob

if __name__ == "__main__":
    BatchRunnerJob().main()
