import os
import sys

# Make the package modules (kv_policy, run_long_dialogue, ...) importable as
# top-level modules in tests without requiring an installed package.
PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)
