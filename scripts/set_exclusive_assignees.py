#!/usr/bin/env python3
"""
Set 100% exclusive, non-overlapping assignees across all 22 GitHub issues.
Jaweria: Issues #5, #6, #14, #15, #16, #17 (Architecture, Concurrency, Static Hotspots)
Mohsin: Issues #3, #4, #7, #8, #9, #10, #11 (API Contracts & Validation)
Aun: Issues #12, #13, #18, #19, #20, #21, #22, #23, #24 (Accessibility, Security, Performance)
"""

import subprocess
import time

EXCLUSIVE_MAP = {
    # Jaweria (Area 1 & Structural Lead)
    5: "Jaweria-Abdul-Hameed",
    6: "Jaweria-Abdul-Hameed",
    14: "Jaweria-Abdul-Hameed",
    15: "Jaweria-Abdul-Hameed",
    16: "Jaweria-Abdul-Hameed",
    17: "Jaweria-Abdul-Hameed",

    # Mohsin Khan (Area 2 API Lead)
    3: "mohsinkhandevs",
    4: "mohsinkhandevs",
    7: "mohsinkhandevs",
    8: "mohsinkhandevs",
    9: "mohsinkhandevs",
    10: "mohsinkhandevs",
    11: "mohsinkhandevs",

    # Muhammad Aun (Area 3 Validation Lead)
    12: "m-aun-005",
    13: "m-aun-005",
    18: "m-aun-005",
    19: "m-aun-005",
    20: "m-aun-005",
    21: "m-aun-005",
    22: "m-aun-005",
    23: "m-aun-005",
    24: "m-aun-005",
}

def main():
    print("Setting 100% exclusive assignees for all 22 issues...")
    for issue_id, assignee in EXCLUSIVE_MAP.items():
        cmd = [
            "gh", "api", "-X", "PATCH",
            f"/repos/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues/{issue_id}",
            "-f", f"assignees[]={assignee}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Issue #{issue_id} -> EXCLUSIVELY assigned to {assignee}")
        else:
            print(f"Issue #{issue_id} failed: {res.stderr}")
        time.sleep(0.5)

    print("All 22 issues exclusively partitioned successfully!")

if __name__ == "__main__":
    main()
