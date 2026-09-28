import sys
import os

# Add repository root directory to sys.path so backend imports work
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Auto-initialize database & seed data on serverless cold-start
try:
    from backend.database.db import init_db, seed_demo_data
    init_db()
    seed_demo_data()
except Exception as e:
    print(f"Vercel DB initialization note: {e}")

from backend.main import app
