import os
import sys

# Add project root directory to sys.path so backend modules can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app

# Vercel looks for the ASGI application variable 'app'
__all__ = ["app"]
