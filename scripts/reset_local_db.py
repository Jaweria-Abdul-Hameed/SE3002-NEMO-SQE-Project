"""Reset local SQLite database, apply migrations, and re-seed synthetic NEMO data."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("NEMO_SQLITE_PATH", str(ROOT_DIR / "sqe_nemo.db")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset NEMO local SQLite DB to clean seeded state.")
    parser.add_argument("--no-samples", action="store_true", help="Seed base users/areas without sample requests.")
    args = parser.parse_args()

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database: {DB_PATH}")

    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "sqe_local.settings"
    env["PYTHONPATH"] = str(ROOT_DIR)

    subprocess.run(
        [sys.executable, str(ROOT_DIR / "manage.py"), "migrate", "--noinput"],
        cwd=str(ROOT_DIR),
        env=env,
        check=True,
    )

    seed_cmd = [sys.executable, str(ROOT_DIR / "scripts" / "seed_synthetic_data.py")]
    if args.no_samples:
        seed_cmd.append("--no-samples")
    subprocess.run(seed_cmd, cwd=str(ROOT_DIR), env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
