"""Run custom nemo_br/* mutation operators (RelaxBuddyMinimumOperator) on NEMO/forms.py via Cosmic Ray."""

import os
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_SCRIPTS = ROOT / "venv" / "Scripts"
CR_EXE = str(VENV_SCRIPTS / "cosmic-ray.exe") if (VENV_SCRIPTS / "cosmic-ray.exe").exists() else "cosmic-ray"
CR_REPORT = str(VENV_SCRIPTS / "cr-report.exe") if (VENV_SCRIPTS / "cr-report.exe").exists() else "cr-report"


def main():
    cfg = ROOT / "cosmic-ray-forms.toml"
    db = ROOT / "docs" / "evidence" / "cr_forms_custom.sqlite"
    report = ROOT / "docs" / "evidence" / "cr_forms_custom_report.txt"
    if db.exists():
        db.unlink()

    env = os.environ.copy()
    env["PATH"] = f"{VENV_SCRIPTS};{env.get('PATH', '')}"

    subprocess.run([CR_EXE, "init", str(cfg), str(db)], cwd=str(ROOT), env=env, check=True)

    conn = sqlite3.connect(db)
    conn.execute(
        "DELETE FROM work_items WHERE job_id IN (SELECT job_id FROM mutation_specs WHERE operator_name NOT LIKE 'nemo_br/%')"
    )
    conn.execute("DELETE FROM mutation_specs WHERE operator_name NOT LIKE 'nemo_br/%'")
    conn.commit()
    specs = conn.execute("SELECT operator_name, start_pos_row FROM mutation_specs").fetchall()
    conn.close()
    print("Filtered custom nemo_br mutants on NEMO/forms.py:", specs)

    subprocess.run([CR_EXE, "exec", str(cfg), str(db)], cwd=str(ROOT), env=env, check=True)
    res = subprocess.run([CR_REPORT, str(db)], cwd=str(ROOT), env=env, capture_output=True, text=True, check=True)
    report.write_text(res.stdout, encoding="utf-8")
    print(res.stdout)


if __name__ == "__main__":
    main()
