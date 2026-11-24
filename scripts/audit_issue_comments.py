#!/usr/bin/env python3
"""
Audit all comments and assignees on GitHub issues #3 to #24.
"""

import subprocess
import json

for num in range(3, 25):
    cmd = ["gh", "api", f"/repos/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues/{num}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        continue
    data = json.loads(res.stdout)
    title = data.get("title", "")
    assignees = [a["login"] for a in data.get("assignees", [])]

    cmd_c = ["gh", "api", f"/repos/Jaweria-Abdul-Hameed/SE3002-NEMO-SQE-Project/issues/{num}/comments"]
    res_c = subprocess.run(cmd_c, capture_output=True, text=True)
    comments = json.loads(res_c.stdout) if res_c.returncode == 0 else []

    print(f"Issue #{num} | Title: {title[:40]} | Assignee: {assignees}")
    for c in comments:
        cid = c["id"]
        author = c["user"]["login"]
        preview = c["body"].replace("\n", " ")[:60]
        print(f"   [ID: {cid}] by @{author}: {preview}...")
