import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(ROOT_DIR, 'vendor')
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
