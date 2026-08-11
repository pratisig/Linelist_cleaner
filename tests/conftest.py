"""
Pytest configuration and environment fixtures for Linelist Cleaner.
Ensures repository root is always in sys.path regardless of execution environment.
"""

import sys
import os

# Add repository root directory to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
