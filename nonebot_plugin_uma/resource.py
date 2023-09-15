import shutil
from pathlib import Path

DATA_PATH = Path.cwd() / "data" / "uma"
CACHE_PATH = DATA_PATH / "cache"

for path in (DATA_PATH, CACHE_PATH):
    if not path.exists():
        path.mkdir(parents=True)

SKILLS_CONFIG_PATH = DATA_PATH / "skills_config.json"


def clear_cache():
    if CACHE_PATH.exists():
        shutil.rmtree(CACHE_PATH)
        CACHE_PATH.mkdir(parents=True)
