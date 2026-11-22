"""Run Cosmic Ray mutation testing across N parallel local `cosmic-ray http-worker` processes.

Area 1 Owner: Jaweria Abdul Hameed (24I-3025)
Uses 100% native Cosmic Ray (`init`, `http-worker`, `exec`, `cr-report`) with isolated
temporary worker directories so each worker mutates its own copy of the target file safely.
"""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_SCRIPTS = ROOT / "venv" / "Scripts"
COSMIC_RAY_EXE = str(VENV_SCRIPTS / "cosmic-ray.exe") if (VENV_SCRIPTS / "cosmic-ray.exe").exists() else "cosmic-ray"
CR_REPORT_EXE = str(VENV_SCRIPTS / "cr-report.exe") if (VENV_SCRIPTS / "cr-report.exe").exists() else "cr-report"
PYTHON_EXE = sys.executable


def _wait_for_port(port: int, timeout: float = 20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"Worker on port {port} did not start within {timeout}s")


def _prepare_worker_dir(worker_dir: Path):
    """Create a minimal isolated working directory containing NEMO, sqe_local, scripts, tests/team, pytest.ini."""
    for folder in ("NEMO", "sqe_local", "scripts"):
        shutil.copytree(ROOT / folder, worker_dir / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(
        ROOT / "tests" / "team",
        worker_dir / "tests" / "team",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (worker_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy2(ROOT / "pytest.ini", worker_dir / "pytest.ini")
    # Copy pre-created test SQLite DB if present so --reuse-db starts immediately
    test_db = ROOT / "sqe_nemo_pytest.db"
    if test_db.exists():
        shutil.copy2(test_db, worker_dir / "sqe_nemo_pytest.db")


def main():
    parser = argparse.ArgumentParser(description="Execute Cosmic Ray using parallel local HTTP workers.")
    parser.add_argument("--module", default="NEMO/views/access_requests.py", help="Target module path to mutate.")
    parser.add_argument("--session", required=True, help="Output Cosmic Ray SQLite session path.")
    parser.add_argument("--report", required=True, help="Output text file for cr-report summary.")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel HTTP workers.")
    parser.add_argument("--base-port", type=int, default=9880, help="Starting TCP port for HTTP workers.")
    parser.add_argument(
        "--test-command",
        default=f'"{PYTHON_EXE}" -m pytest -x -q --reuse-db --nomigrations tests/team/unit',
        help="Test command executed by each worker.",
    )
    parser.add_argument("--fresh", action="store_true", help="Re-initialize session DB from scratch.")
    args = parser.parse_args()

    session_path = Path(args.session).resolve()
    report_path = Path(args.report).resolve()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure root sqe_nemo_pytest.db exists so workers inherit it
    if not (ROOT / "sqe_nemo_pytest.db").exists():
        subprocess.run(
            [PYTHON_EXE, "-m", "pytest", "-q", "--create-db", "--nomigrations", "tests/team/unit/test_baseline_smoke.py"],
            cwd=str(ROOT),
            check=True,
        )

    worker_urls = [f"http://127.0.0.1:{args.base_port + i}" for i in range(args.workers)]
    toml_content = f"""[cosmic-ray]
module-path = "{args.module}"
timeout = 90.0
excluded-modules = []
test-command = '{args.test_command}'

[cosmic-ray.distributor]
name = "http"

[cosmic-ray.distributor.http]
worker-urls = {worker_urls!r}
"""

    tmp_root = Path(tempfile.mkdtemp(prefix="cr_workers_"))
    cfg_path = tmp_root / "cosmic-ray-http.toml"
    cfg_path.write_text(toml_content, encoding="utf-8")

    procs = []
    try:
        if args.fresh and session_path.exists():
            session_path.unlink()
        if not session_path.exists():
            print(f"[1/4] Initializing Cosmic Ray session {session_path} for {args.module}...")
            subprocess.run([COSMIC_RAY_EXE, "init", str(cfg_path), str(session_path)], cwd=str(ROOT), check=True)

        print(f"[2/4] Preparing {args.workers} isolated worker directories & starting http-workers...")
        for idx in range(args.workers):
            wdir = tmp_root / f"worker_{idx}"
            wdir.mkdir(parents=True, exist_ok=True)
            _prepare_worker_dir(wdir)
            port = args.base_port + idx
            env = os.environ.copy()
            env["PYTHONPATH"] = str(wdir)
            env["PATH"] = f"{VENV_SCRIPTS};{env.get('PATH', '')}"
            proc = subprocess.Popen(
                [COSMIC_RAY_EXE, "http-worker", "--port", str(port)],
                cwd=str(wdir),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            procs.append(proc)

        for idx in range(args.workers):
            _wait_for_port(args.base_port + idx)
        print(f"      All {args.workers} workers ready on ports {args.base_port}..{args.base_port + args.workers - 1}.")

        t0 = time.time()
        print(f"[3/4] Running `cosmic-ray exec` across {args.workers} workers...")
        subprocess.run([COSMIC_RAY_EXE, "exec", str(cfg_path), str(session_path)], cwd=str(ROOT), check=True)
        elapsed = time.time() - t0
        print(f"      Completed in {elapsed:.1f}s.")

        print(f"[4/4] Generating `cr-report` -> {report_path}")
        res = subprocess.run([CR_REPORT_EXE, str(session_path)], cwd=str(ROOT), capture_output=True, text=True, check=True)
        report_path.write_text(res.stdout, encoding="utf-8")
        print(res.stdout[-2000:])
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
