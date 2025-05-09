#default_app_config = 'core.apps.CoreConfig' 


import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent # This is b2b_marketplace_project/marketplace_api/
PROJECT_ROOT = BASE_DIR.parent # This should be b2b_marketplace_project/

# print(f"PROJECT_ROOT is: {PROJECT_ROOT}")
# print(f"Current sys.path: {sys.path}")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    # print(f"Added {PROJECT_ROOT} to sys.path")
# else:
    # print(f"{PROJECT_ROOT} already in sys.path")