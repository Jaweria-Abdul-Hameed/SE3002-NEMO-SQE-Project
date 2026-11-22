"""Demonstrate OpenAPI two-constraint regeneration & diff for Phase 4 / Viva readiness.

Area 2 Owner: Mohsin Khan (24I-3135)
Changes two constraints in a derived copy of the OpenAPI specification:
  1. other_users.minItems: 1 -> 2  (reflecting access_requests_minimum_users = 3)
  2. description.maxLength: 500 -> 200
Re-runs `scripts/generate_api_test_data.py` and writes the exact before/after diff.
"""

import copy
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_api_test_data import generate_dataset


def main():
    base_spec_path = ROOT / "openapi" / "temporary_physical_access_requests.yaml"
    demo_dir = ROOT / "docs" / "evidence" / "openapi_regeneration_demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    mutated_spec_path = ROOT / "openapi" / "temporary_physical_access_requests_two_constraints_demo.yaml"

    spec = yaml.safe_load(base_spec_path.read_text(encoding="utf-8"))
    mutated_spec = copy.deepcopy(spec)
    write_props = mutated_spec["components"]["schemas"]["TemporaryPhysicalAccessRequestWrite"]["properties"]
    patch_props = mutated_spec["components"]["schemas"]["TemporaryPhysicalAccessRequestPatch"]["properties"]

    # Constraint Change 1: other_users.minItems 1 -> 2
    write_props["other_users"]["minItems"] = 2
    patch_props["other_users"]["minItems"] = 2

    # Constraint Change 2: description.maxLength 500 -> 200
    write_props["description"]["maxLength"] = 200
    patch_props["description"]["maxLength"] = 200

    mutated_spec["info"]["version"] = "8.2.1-sqe-2constraint-demo"
    mutated_spec_path.write_text(yaml.safe_dump(mutated_spec, sort_keys=False), encoding="utf-8")

    before = generate_dataset(base_spec_path)
    after = generate_dataset(mutated_spec_path)

    (demo_dir / "generated_before.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    (demo_dir / "generated_after.json").write_text(json.dumps(after, indent=2), encoding="utf-8")

    before_bva = {c["case_id"]: c for c in before["body_bva_cases"]}
    after_bva = {c["case_id"]: c for c in after["body_bva_cases"]}
    changed_bva = []
    for cid in sorted(set(before_bva) | set(after_bva)):
        b_item = before_bva.get(cid)
        a_item = after_bva.get(cid)
        if b_item != a_item:
            changed_bva.append(
                {
                    "case_id": cid,
                    "before": {k: b_item.get(k) for k in ("boundary", "point", "length", "item_count", "expected_valid")}
                    if b_item
                    else None,
                    "after": {k: a_item.get(k) for k in ("boundary", "point", "length", "item_count", "expected_valid")}
                    if a_item
                    else None,
                }
            )

    diff_report = {
        "constraint_changes": [
            {"field": "other_users", "constraint": "minItems", "before": 1, "after": 2},
            {"field": "description", "constraint": "maxLength", "before": 500, "after": 200},
        ],
        "before_spec_sha256": before["meta"]["spec_sha256_16"],
        "after_spec_sha256": after["meta"]["spec_sha256_16"],
        "baseline_payload_other_users_before": before["baseline_valid_payload"]["other_users"],
        "baseline_payload_other_users_after": after["baseline_valid_payload"]["other_users"],
        "changed_bva_cases": changed_bva,
    }
    diff_path = demo_dir / "regeneration_diff.json"
    diff_path.write_text(json.dumps(diff_report, indent=2), encoding="utf-8")

    print(f"Wrote mutated spec: {mutated_spec_path}")
    print(f"Wrote diff report:  {diff_path}")
    print(f"Baseline other_users template: {diff_report['baseline_payload_other_users_before']} -> {diff_report['baseline_payload_other_users_after']}")
    print(f"Changed 3-Point BVA cases ({len(changed_bva)}):")
    for item in changed_bva:
        print(f"  {item['case_id']}: {item['before']} -> {item['after']}")


if __name__ == "__main__":
    main()
