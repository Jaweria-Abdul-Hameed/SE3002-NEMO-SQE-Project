"""Run 4 comparable Grafana k6 OSS load benchmarks (1 VU x 2, 5 VUs x 2, >=60s each) on identical starting state."""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT_DIR / "docs" / "evidence" / "phase6"
PYTHON_EXE = str(ROOT_DIR / "venv" / "Scripts" / "python.exe")


def find_k6() -> str:
    found = shutil.which("k6")
    if found:
        return found
    default_win = Path(r"C:\Program Files\k6\k6.exe")
    if default_win.exists():
        return str(default_win)
    raise FileNotFoundError("k6 binary not found on PATH or C:\\Program Files\\k6\\k6.exe")


def wait_http(url: str, timeout: int = 45) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for {url}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    k6_exe = find_k6()
    k6_ver = subprocess.check_output([k6_exe, "version"], text=True).strip()

    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "sqe_local.settings"

    runs = [
        {"name": "1vu_run1", "vus": 1, "duration": "65s"},
        {"name": "1vu_run2", "vus": 1, "duration": "65s"},
        {"name": "5vu_run1", "vus": 5, "duration": "65s"},
        {"name": "5vu_run2", "vus": 5, "duration": "65s"},
    ]

    results = []
    for run in runs:
        # Reset DB cleanly before each run so every benchmark uses identical starting data
        subprocess.run([PYTHON_EXE, str(ROOT_DIR / "scripts" / "e2e_db_helper.py"), "reset"], check=True)

        server_proc = subprocess.Popen(
            [PYTHON_EXE, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
            cwd=str(ROOT_DIR),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_http("http://127.0.0.1:8000/login/")
            summary_path = OUT_DIR / f"k6_{run['name']}_summary.json"
            txt_path = OUT_DIR / f"k6_{run['name']}.txt"

            cmd = [
                k6_exe,
                "run",
                "--env",
                "BASE_URL=http://127.0.0.1:8000",
                "--env",
                f"VUS={run['vus']}",
                "--env",
                f"DURATION={run['duration']}",
                "--summary-export",
                str(summary_path),
                str(ROOT_DIR / "tests" / "team" / "performance" / "access_requests_load.js"),
            ]
            print(f"Running {run['name']} (VUs={run['vus']}, duration={run['duration']})...")
            proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
            txt_path.write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")

            summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
            metrics = summary_data.get("metrics", {})
            dur = metrics.get("http_req_duration{endpoint:access_requests}", metrics.get("http_req_duration", {}))
            reqs = metrics.get("http_reqs", {})
            failed = metrics.get("http_req_failed", {})
            results.append(
                {
                    "run": run["name"],
                    "vus": run["vus"],
                    "duration": run["duration"],
                    "exit_code": proc.returncode,
                    "p95_ms": round(float(dur.get("p(95)", 0.0)), 3),
                    "avg_ms": round(float(dur.get("avg", 0.0)), 3),
                    "rps": round(float(reqs.get("rate", 0.0)), 3),
                    "total_requests": int(reqs.get("count", 0)),
                    "unexpected_failure_pct": round(float(failed.get("value", 0.0)) * 100.0, 4),
                }
            )
            print("  Result:", results[-1])
        finally:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=10)
            except Exception:
                server_proc.kill()

    meta = {
        "k6_version": k6_ver,
        "os": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "target_operation": "GET /access_requests/ (authenticated as lab_user)",
        "targets": {"p95_limit_ms": 500, "max_unexpected_failure_pct": 1.0},
        "runs": results,
    }
    (OUT_DIR / "k6_environment_and_summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
