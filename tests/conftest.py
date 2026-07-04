import sys
import os

# Add scripts directory to path so that tests can import scripts directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
