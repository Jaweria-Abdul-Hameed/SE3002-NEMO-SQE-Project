"""Fetch real SonarQube metrics for project and in-scope files and save raw JSON."""

import json
import os
import sys
from pathlib import Path

import requests

SONAR_URL = os.getenv("SONAR_HOST_URL", "http://localhost:9090")
SONAR_USER = os.getenv("SONAR_USER", "admin")
SONAR_PASS = os.getenv("SONAR_PASSWORD", "SqeSonarAdmin!2026")
PROJECT_KEY = os.getenv("SONAR_PROJECT_KEY", "nemo-sqe-access-requests")

METRIC_KEYS = ",".join(
    [
        "ncloc",
        "lines",
        "statements",
        "functions",
        "classes",
        "complexity",
        "cognitive_complexity",
        "duplicated_lines_density",
        "duplicated_blocks",
        "code_smells",
        "bugs",
        "vulnerabilities",
        "security_hotspots",
        "coverage",
        "line_coverage",
        "branch_coverage",
        "sqale_index",
        "sqale_rating",
        "reliability_rating",
        "security_rating",
        "security_review_rating",
        "alert_status",
    ]
)


def fetch_component(component_key: str) -> dict:
    resp = requests.get(
        f"{SONAR_URL}/api/measures/component",
        params={"component": component_key, "metricKeys": METRIC_KEYS},
        auth=(SONAR_USER, SONAR_PASS),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_issues(component_key: str) -> dict:
    resp = requests.get(
        f"{SONAR_URL}/api/issues/search",
        params={"componentKeys": component_key, "ps": 100},
        auth=(SONAR_USER, SONAR_PASS),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    out_dir = Path("docs/evidence")
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "project": fetch_component(PROJECT_KEY),
        "access_requests_py": fetch_component(f"{PROJECT_KEY}:NEMO/views/access_requests.py"),
        "forms_py": fetch_component(f"{PROJECT_KEY}:NEMO/forms.py"),
        "models_py": fetch_component(f"{PROJECT_KEY}:NEMO/models.py"),
        "api_py": fetch_component(f"{PROJECT_KEY}:NEMO/views/api.py"),
        "access_requests_issues": fetch_issues(f"{PROJECT_KEY}:NEMO/views/access_requests.py"),
    }
    out_path = out_dir / "sonarqube_baseline_metrics.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved SonarQube metrics to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
