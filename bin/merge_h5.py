#!/usr/bin/env python3
import sys
import os

# command/ を PYTHONPATH に追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from module.merge_h5.merge_h5 import MergeH5Job

if __name__ == "__main__":
    MergeH5Job().main()
