"""Orchestrate OWASP ZAP passive scan while Playwright executes both NEMO workflows."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT_DIR / "docs" / "evidence" / "phase6"
PYTHON_EXE = str(ROOT_DIR / "venv" / "Scripts" / "python.exe")
CONTAINER_NAME = "nemo-zap-passive"


def wait_http(url: str, timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"Timed out waiting for {url}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run([PYTHON_EXE, str(ROOT_DIR / "scripts" / "e2e_db_helper.py"), "reset"], check=True)

    # Remove stale container if present
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "sqe_local.settings"

    server_proc = subprocess.Popen(
        [PYTHON_EXE, "manage.py", "runserver", "0.0.0.0:8000", "--noreload"],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_http("http://127.0.0.1:8000/login/", timeout=45)

        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                CONTAINER_NAME,
                "-p",
                "8090:8090",
                "--add-host=host.docker.internal:host-gateway",
                "ghcr.io/zaproxy/zaproxy:stable",
                "zap.sh",
                "-daemon",
                "-host",
                "0.0.0.0",
                "-port",
                "8090",
                "-config",
                "api.addrs.addr.name=.*",
                "-config",
                "api.addrs.addr.regex=true",
                "-config",
                "api.disablekey=true",
            ],
            check=True,
        )

        wait_http("http://127.0.0.1:8090/JSON/core/view/version/", timeout=90)
        print("OWASP ZAP daemon ready on 127.0.0.1:8090")

        pw_env = env.copy()
        pw_env["SKIP_WEB_SERVER"] = "1"
        pw_env["PLAYWRIGHT_BASE_URL"] = "http://host.docker.internal:8000"
        pw_env["PLAYWRIGHT_PROXY_SERVER"] = "http://127.0.0.1:8090"

        subprocess.run(
            [
                "node",
                "node_modules/@playwright/test/cli.js",
                "test",
                "tests/team/usability/usability_and_keyboard.spec.mjs",
                "tests/team/security/role_checks.spec.mjs",
            ],
            cwd=str(ROOT_DIR),
            env=pw_env,
            check=True,
        )

        # Wait for ZAP passive scan queue to drain
        for _ in range(60):
            with urlopen("http://127.0.0.1:8090/JSON/pscan/view/recordsToScan/") as r:
                rem = int(json.loads(r.read().decode("utf-8"))["recordsToScan"])
                if rem == 0:
                    break
            time.sleep(0.5)

        with urlopen("http://127.0.0.1:8090/JSON/core/view/alerts/?baseurl=http://host.docker.internal:8000") as r:
            alerts = json.loads(r.read().decode("utf-8"))
        with urlopen("http://127.0.0.1:8090/JSON/alert/view/alertsSummary/?baseurl=http://host.docker.internal:8000") as r:
            summary = json.loads(r.read().decode("utf-8"))
        with urlopen("http://127.0.0.1:8090/OTHER/core/other/htmlreport/") as r:
            html_report = r.read()

        (OUT_DIR / "zap_passive_alerts.json").write_text(json.dumps(alerts, indent=2), encoding="utf-8")
        (OUT_DIR / "zap_passive_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (OUT_DIR / "zap_passive_report.html").write_bytes(html_report)
        print("ZAP summary:", summary)
        print("ZAP alert count:", len(alerts.get("alerts", [])))
    finally:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        server_proc.terminate()
        try:
            server_proc.wait(timeout=10)
        except Exception:
            server_proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
