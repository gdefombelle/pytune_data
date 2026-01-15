from functools import lru_cache
from pathlib import Path
from typing import Dict, Any
import yaml

PLANS_FILE = (
    Path(__file__).resolve()
    .parents[1] / "policies" / "plans.yaml"
)

# @lru_cache(maxsize=1)
def load_plans_catalog() -> Dict[str, Any]:
    if not PLANS_FILE.exists():
        raise RuntimeError(f"Plans file not found: {PLANS_FILE}")

    with open(PLANS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "plans" not in data:
        raise RuntimeError("Invalid plans.yaml format")

    return data["plans"]