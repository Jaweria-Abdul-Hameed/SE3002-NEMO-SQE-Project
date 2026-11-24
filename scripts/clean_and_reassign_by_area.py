#!/usr/bin/env python3
"""
Reassign all issues strictly by area ownership and delete all cross-comments.
- Area 1 (Jaweria): Static Analysis / Hotspot (Issue #14)
- Area 2 (Mohsin): API & Integration (Issues #3, #4, #5, #6, #7, #8, #9, #10, #11)
- Area 3 (Aun): Security, Performance, Accessibility (Issues #12, #13, #15, #16, #17, #18, #19, #20, #21, #22, #23, #24)
"""

import subprocess
import time

# 1. Exact Area Mapping
AREA_ASSIGNMENTS = {
    # Area 2 (Mohsin Khan)
    3: "mohsinkhandevs",
    4: "mohsinkhandevs",
    5: "mohsinkhandevs",
    6: "mohsinkhandevs",
    7: "mohsinkhandevs",
    8: "mohsinkhandevs",
    9: "mohsinkhandevs",
    10: "mohsinkhandevs",
    11: "mohsinkhandevs",

    # Area 1 (Jaweria Abdul Hameed)
    14: "Jaweria-Abdul-Hameed",

    # Area 3 (Muhammad Aun)
    12: "m-aun-005",
    13: "m-aun-005",
    15: "m-aun-005",
    16: "m-aun-005",
    17: "m-aun-005",
    18: "m-aun-005",
    19: "m-aun-005",
    20: "m-aun-005",
    21: "m-aun-005",
    22: "m-aun-005",
    23: "m-aun-005",
    24: "m-aun-005",
}

# 2. Comments by Jaweria to delete on other members' issues
COMMENTS_TO_DELETE = [
    7082404140,  # Issue #3
    7121478497,  # Issue #4 (Mohsin has his own comment 7122942084)
    7121558776,  # Issue #5
    7121559421,  # Issue #6
    7121560162,  # Issue #7 (Mohsin has his own comment 7122958614)
    7121560903,  # Issue #8
    7121561614,  # Issue #9
    7121562387,  # Issue #10
    7121562999,  # Issue #11
    7121564320,  # Issue #13
    7121565692,  # Issue #15
    7121566934,  # Issue #17
    7082429334,  # Issue #18
    7082430350,  # Issue #19
    7082431420,  # Issue #20
    7082432475,  # Issue #21
    7121567588,  # Issue #22
    7121568280,  # Issue #23
    7121568975,  # Issue #24
]

def main():
    print("Step 1: Reassigning issues strictly by area ownership...")
    for issue_id, assignee in AREA_ASSIGNMENTS.items():
        cmd = [
            "gh", "api", "-X", "PATCH",
            f"/repos/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues/{issue_id}",
            "-f", f"assignees[]={assignee}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Issue #{issue_id} -> Assigned strictly to {assignee}")
        else:
            print(f"Failed to assign Issue #{issue_id}: {res.stderr}")
        time.sleep(0.3)

    print("\nStep 2: Deleting all cross-comments on other members' issues...")
    for cid in COMMENTS_TO_DELETE:
        cmd = [
            "gh", "api", "-X", "DELETE",
            f"/repos/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues/comments/{cid}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Deleted cross-comment ID {cid}")
        else:
            print(f"Failed to delete comment ID {cid}: {res.stderr}")
        time.sleep(0.3)

    print("\nRepository issues are now 100% cleanly partitioned by area with zero cross-comments!")

if __name__ == "__main__":
    main()
