import os

# Paths
# Assumes this config.py is in src/ directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(BASE_DIR, "json")
OPT_DIR = os.path.join(BASE_DIR, "opt")
UIDS_FILE = os.path.join(BASE_DIR, "uids.xlsx")
OUTPUT_FILE = os.path.join(OPT_DIR, "luogu_analysis.xlsx")

# Luogu Config
LUOGU_BASE_URL = "https://www.luogu.com.cn/record/list"
