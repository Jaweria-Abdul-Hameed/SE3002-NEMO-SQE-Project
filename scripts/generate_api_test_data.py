"""Spec-Driven OpenAPI 3.0 Equivalence Partitioning (EP) & 3-Point BVA Test Data Generator.

Area 2 Owner: Mohsin Khan (24I-3135)
Usage:
    python scripts/generate_api_test_data.py \
        --spec openapi/temporary_physical_access_requests.yaml \
        --output tests/team/api/generated_test_data.json

Designed for live Viva adaptability:
    Change any constraint (minItems, maxItems, minLength, maxLength, minimum,
    maximum, enum, required, nullable, x-min-offset-minutes, x-min-duration-minutes,
    x-max-duration-hours, x-state-transitions) in any OpenAPI 3.0 YAML/JSON file
    and re-run this script to regenerate all EP partitions, 3-point BVA values,
    query/path parameter cases, and state-transition test cases automatically.
"""

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


def load_spec(spec_path: Path) -> tuple[dict[str, Any], str]:
    raw_text = spec_path.read_text(encoding="utf-8")
    spec = yaml.safe_load(raw_text)
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:16]
    return spec, digest


def resolve_ref(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    if "$ref" not in schema:
        return schema
    ref_path = schema["$ref"].lstrip("#/").split("/")
    node: Any = spec
    for part in ref_path:
        node = node[part]
    return node


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_valid_sample_value(prop_name: str, prop_schema: dict[str, Any], anchor_now: datetime) -> Any:
    """Build a valid nominal value strictly satisfying all schema constraints."""
    ptype = prop_schema.get("type")
    fmt = prop_schema.get("format")

    if "enum" in prop_schema:
        return prop_schema.get("default", prop_schema["enum"][0])

    if ptype == "boolean":
        return prop_schema.get("default", False)

    if ptype == "integer":
        if "x-seed-ref" in prop_schema:
            return f"${{{prop_schema['x-seed-ref']}}}"
        lo = prop_schema.get("minimum", 1)
        hi = prop_schema.get("maximum", lo + 10)
        return min(max(lo, 1), hi)

    if ptype == "string":
        if fmt == "date-time":
            if "x-must-be-after" in prop_schema:
                min_dur = int(prop_schema.get("x-min-duration-minutes", 1))
                max_hrs = int(prop_schema.get("x-max-duration-hours", 168))
                dur_minutes = min(max(min_dur + 60, 120), max_hrs * 60)
                return f"${{rel_start_plus_minutes:{dur_minutes}}}"
            offset_min = int(prop_schema.get("x-min-offset-minutes", 0))
            return f"${{rel_now_plus_minutes:{max(offset_min + 60, 1440)}}}"
        min_len = int(prop_schema.get("minLength", 1))
        max_len = int(prop_schema.get("maxLength", max(min_len + 20, 64)))
        base_str = f"Synthetic valid {prop_name} payload"
        if len(base_str) < min_len:
            base_str = base_str + ("x" * (min_len - len(base_str)))
        return base_str[:max_len]

    if ptype == "array":
        min_items = int(prop_schema.get("minItems", 0))
        count = max(min_items, 1)
        if "x-seed-ref" in prop_schema:
            return f"${{{prop_schema['x-seed-ref']}:{count}}}"
        return [i + 1 for i in range(count)]

    return None


def generate_ep_for_property(
    field_name: str,
    prop_schema: dict[str, Any],
    is_required: bool,
) -> list[dict[str, Any]]:
    """Generate Equivalence Partitioning (EP) cases — one invalid value per case."""
    cases: list[dict[str, Any]] = []
    ptype = prop_schema.get("type")
    fmt = prop_schema.get("format")
    nullable = bool(prop_schema.get("nullable", False))

    if is_required:
        cases.append(
            {
                "case_id": f"EP-{field_name}-missing-required",
                "technique": "EP",
                "field": field_name,
                "partition": "missing_required_field",
                "expected_valid": False,
                "omit_field": True,
                "value": None,
                "rationale": f"Required field '{field_name}' omitted from request body.",
            }
        )

    if nullable:
        cases.append(
            {
                "case_id": f"EP-{field_name}-null-allowed",
                "technique": "EP",
                "field": field_name,
                "partition": "valid_null",
                "expected_valid": True,
                "value": None,
                "rationale": f"Field '{field_name}' declares nullable: true.",
            }
        )
    else:
        cases.append(
            {
                "case_id": f"EP-{field_name}-null-disallowed",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_null",
                "expected_valid": False,
                "value": None,
                "rationale": f"Field '{field_name}' is non-nullable.",
            }
        )

    if "enum" in prop_schema:
        enum_vals = prop_schema["enum"]
        for val in enum_vals:
            cases.append(
                {
                    "case_id": f"EP-{field_name}-enum-valid-{val}",
                    "technique": "EP",
                    "field": field_name,
                    "partition": f"valid_enum_{val}",
                    "expected_valid": True,
                    "value": val,
                    "rationale": f"Valid enum member {val} in {enum_vals}.",
                }
            )
        invalid_enum = (max(enum_vals) + 10) if all(isinstance(v, int) for v in enum_vals) else "INVALID_ENUM"
        cases.append(
            {
                "case_id": f"EP-{field_name}-enum-invalid",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_enum_value",
                "expected_valid": False,
                "value": invalid_enum,
                "rationale": f"Value {invalid_enum} outside allowed enum {enum_vals}.",
            }
        )

    if ptype == "integer":
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-type-string",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_type_string",
                "expected_valid": False,
                "value": "not-an-integer",
                "rationale": f"Non-integer string supplied for integer field '{field_name}'.",
            }
        )
        if "x-seed-ref" in prop_schema:
            cases.append(
                {
                    "case_id": f"EP-{field_name}-valid-fk",
                    "technique": "EP",
                    "field": field_name,
                    "partition": "valid_existing_reference",
                    "expected_valid": True,
                    "value": f"${{{prop_schema['x-seed-ref']}}}",
                    "rationale": f"Valid existing primary key reference for '{field_name}'.",
                }
            )
            cases.append(
                {
                    "case_id": f"EP-{field_name}-nonexistent-fk",
                    "technique": "EP",
                    "field": field_name,
                    "partition": "invalid_nonexistent_fk",
                    "expected_valid": False,
                    "value": 999998,
                    "rationale": f"Non-existent foreign key ID for '{field_name}'.",
                }
            )

    elif ptype == "string" and fmt == "date-time":
        cases.append(
            {
                "case_id": f"EP-{field_name}-valid-iso-datetime",
                "technique": "EP",
                "field": field_name,
                "partition": "valid_iso_datetime",
                "expected_valid": True,
                "value": build_valid_sample_value(field_name, prop_schema, datetime.now(timezone.utc)),
                "rationale": f"Valid ISO-8601 date-time satisfying temporal constraints for '{field_name}'.",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-format",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_datetime_format",
                "expected_valid": False,
                "value": "not-a-valid-datetime",
                "rationale": "Malformed date-time string.",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-calendar-date",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_calendar_date",
                "expected_valid": False,
                "value": "2026-02-30T12:00:00Z",
                "rationale": "Impossible calendar date (Feb 30).",
            }
        )

    elif ptype == "string":
        min_l = int(prop_schema.get("minLength", 1))
        max_l = int(prop_schema.get("maxLength", 500))
        mid_l = max(min_l, min((min_l + max_l) // 2, 40))
        cases.append(
            {
                "case_id": f"EP-{field_name}-valid-nominal",
                "technique": "EP",
                "field": field_name,
                "partition": "valid_string_nominal",
                "expected_valid": True,
                "value": "A" * mid_l,
                "rationale": f"Nominal valid string of length {mid_l} within [{min_l}, {max_l}].",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-type-object",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_type_object",
                "expected_valid": False,
                "value": {"unexpected": "object"},
                "rationale": f"JSON object supplied for string field '{field_name}'.",
            }
        )

    elif ptype == "array":
        min_i = int(prop_schema.get("minItems", 0))
        max_i = int(prop_schema.get("maxItems", 10))
        nom = max(min_i, min(max_i, min_i + 1))
        cases.append(
            {
                "case_id": f"EP-{field_name}-valid-array",
                "technique": "EP",
                "field": field_name,
                "partition": f"valid_array_len_{nom}",
                "expected_valid": True,
                "value": f"${{{prop_schema.get('x-seed-ref', 'buddy_user_ids')}:{nom}}}",
                "rationale": f"Valid array with {nom} item(s) within [{min_i}, {max_i}].",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-item-type",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_array_item_type",
                "expected_valid": False,
                "value": ["non-int-user-id"],
                "rationale": "Array element fails integer item schema.",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-nonexistent-item-fk",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_array_item_fk",
                "expected_valid": False,
                "value": [999997],
                "rationale": "Array element references non-existent user ID.",
            }
        )

    elif ptype == "boolean":
        cases.append(
            {
                "case_id": f"EP-{field_name}-valid-true",
                "technique": "EP",
                "field": field_name,
                "partition": "valid_boolean_true",
                "expected_valid": True,
                "value": True,
                "rationale": "Boolean true partition.",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-valid-false",
                "technique": "EP",
                "field": field_name,
                "partition": "valid_boolean_false",
                "expected_valid": True,
                "value": False,
                "rationale": "Boolean false partition.",
            }
        )
        cases.append(
            {
                "case_id": f"EP-{field_name}-invalid-boolean",
                "technique": "EP",
                "field": field_name,
                "partition": "invalid_boolean_string",
                "expected_valid": False,
                "value": "not-a-bool",
                "rationale": "Non-boolean string for boolean field.",
            }
        )

    return cases


def generate_3point_bva_for_property(field_name: str, prop_schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate strict 3-point BVA (just below, exactly at, just above) for EVERY limit on a property."""
    cases: list[dict[str, Any]] = []
    ptype = prop_schema.get("type")
    fmt = prop_schema.get("format")

    if ptype == "integer":
        if "minimum" in prop_schema:
            lo = int(prop_schema["minimum"])
            is_fk = "x-seed-ref" in prop_schema
            for label, val, expected in [
                ("below_min", lo - 1, False),
                ("at_min", lo, True if not is_fk else True),
                ("above_min", lo + 1, True if ("maximum" not in prop_schema or lo + 1 <= prop_schema["maximum"]) else False),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-min-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"minimum={lo}",
                        "point": label,
                        "value": val,
                        "expected_valid": expected,
                        "fk_sensitive": is_fk,
                        "rationale": f"3-point BVA around minimum={lo}: value={val}.",
                    }
                )
        if "maximum" in prop_schema:
            hi = int(prop_schema["maximum"])
            is_fk = "x-seed-ref" in prop_schema
            for label, val, expected in [
                ("below_max", hi - 1, True),
                ("at_max", hi, True),
                ("above_max", hi + 1, False),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-max-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"maximum={hi}",
                        "point": label,
                        "value": val,
                        "expected_valid": expected,
                        "fk_sensitive": is_fk,
                        "rationale": f"3-point BVA around maximum={hi}: value={val}.",
                    }
                )

    elif ptype == "string" and fmt != "date-time":
        if "minLength" in prop_schema:
            min_l = int(prop_schema["minLength"])
            points = [
                ("below_minLength", max(0, min_l - 1), False if min_l > 0 else True),
                ("at_minLength", min_l, True),
                ("above_minLength", min_l + 1, True),
            ]
            for label, length, expected in points:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-minLength-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"minLength={min_l}",
                        "point": label,
                        "length": length,
                        "value": "D" * length,
                        "expected_valid": expected,
                        "rationale": f"3-point BVA around minLength={min_l}: len={length}.",
                    }
                )
        if "maxLength" in prop_schema:
            max_l = int(prop_schema["maxLength"])
            for label, length, expected in [
                ("below_maxLength", max_l - 1, True),
                ("at_maxLength", max_l, True),
                ("above_maxLength", max_l + 1, False),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-maxLength-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"maxLength={max_l}",
                        "point": label,
                        "length": length,
                        "value": "X" * length,
                        "expected_valid": expected,
                        "rationale": f"3-point BVA around maxLength={max_l}: len={length}.",
                    }
                )

    elif ptype == "string" and fmt == "date-time":
        if "x-min-offset-minutes" in prop_schema:
            off = int(prop_schema["x-min-offset-minutes"])
            for label, delta_min, expected in [
                ("below_min_offset", off - 60, False),
                ("at_min_offset", off, True),
                ("above_min_offset", off + 60, True),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-offset-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"x-min-offset-minutes={off}",
                        "point": label,
                        "value": f"${{rel_now_plus_minutes:{delta_min}}}",
                        "expected_valid": expected,
                        "business_rule": "BR-1 (start_time >= now)",
                        "rationale": f"3-point BVA around start_time offset={off}m: delta={delta_min}m.",
                    }
                )
        if "x-min-duration-minutes" in prop_schema:
            min_d = int(prop_schema["x-min-duration-minutes"])
            for label, delta_min, expected in [
                ("below_min_duration_negative", -1, False),
                ("at_zero_duration_equal", 0, False),
                ("at_min_duration", min_d, True),
                ("above_min_duration", min_d + 1, True),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-minDuration-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"x-min-duration-minutes={min_d}",
                        "point": label,
                        "value": f"${{rel_start_plus_minutes:{delta_min}}}",
                        "expected_valid": expected,
                        "business_rule": "BR-1 (end_time > start_time)",
                        "rationale": f"3-point BVA around min duration={min_d}m: end = start + {delta_min}m.",
                    }
                )
        if "x-max-duration-hours" in prop_schema:
            max_h = int(prop_schema["x-max-duration-hours"])
            max_m = max_h * 60
            for label, delta_min, expected in [
                ("below_max_duration", max_m - 1, True),
                ("at_max_duration", max_m, True),
                ("above_max_duration", max_m + 1, False),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-maxDuration-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"x-max-duration-hours={max_h}",
                        "point": label,
                        "value": f"${{rel_start_plus_minutes:{delta_min}}}",
                        "expected_valid": expected,
                        "business_rule": "BR-1 (max window duration)",
                        "rationale": f"3-point BVA around max duration={max_h}h ({max_m}m): end = start + {delta_min}m.",
                    }
                )

    elif ptype == "array":
        seed_ref = prop_schema.get("x-seed-ref", "buddy_user_ids")
        if "minItems" in prop_schema:
            min_i = int(prop_schema["minItems"])
            for label, count, expected in [
                ("below_minItems", max(0, min_i - 1), False if min_i > 0 else True),
                ("at_minItems", min_i, True),
                ("above_minItems", min_i + 1, True),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-minItems-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"minItems={min_i}",
                        "point": label,
                        "item_count": count,
                        "value": f"${{{seed_ref}:{count}}}",
                        "expected_valid": expected,
                        "business_rule": "BR-1 (access_requests_minimum_users)",
                        "rationale": f"3-point BVA around minItems={min_i}: count={count}.",
                    }
                )
        if "maxItems" in prop_schema:
            max_i = int(prop_schema["maxItems"])
            for label, count, expected in [
                ("below_maxItems", max_i - 1, True),
                ("at_maxItems", max_i, True),
                ("above_maxItems", max_i + 1, False),
            ]:
                cases.append(
                    {
                        "case_id": f"BVA3-{field_name}-maxItems-{label}",
                        "technique": "3-Point BVA",
                        "field": field_name,
                        "boundary": f"maxItems={max_i}",
                        "point": label,
                        "item_count": count,
                        "value": f"${{{seed_ref}:{count}}}",
                        "expected_valid": expected,
                        "business_rule": "BR-1 (max buddies limit)",
                        "rationale": f"3-point BVA around maxItems={max_i}: count={count}.",
                    }
                )

    return cases


def generate_dataset(spec_path: Path) -> dict[str, Any]:
    spec, spec_hash = load_spec(spec_path)
    anchor_now = datetime.now(timezone.utc)

    write_schema = resolve_ref(
        spec,
        {"$ref": "#/components/schemas/TemporaryPhysicalAccessRequestWrite"},
    )
    required_fields = set(write_schema.get("required", []))
    properties = write_schema.get("properties", {})

    baseline_payload = {
        name: build_valid_sample_value(name, prop, anchor_now)
        for name, prop in properties.items()
    }

    body_ep_cases: list[dict[str, Any]] = []
    body_bva_cases: list[dict[str, Any]] = []
    constraints_snapshot: dict[str, dict[str, Any]] = {}

    for prop_name, prop_schema in properties.items():
        constraints_snapshot[prop_name] = {
            k: v
            for k, v in prop_schema.items()
            if k
            in (
                "type",
                "format",
                "nullable",
                "enum",
                "minimum",
                "maximum",
                "minLength",
                "maxLength",
                "minItems",
                "maxItems",
                "x-min-offset-minutes",
                "x-min-duration-minutes",
                "x-max-duration-hours",
            )
        }
        body_ep_cases.extend(generate_ep_for_property(prop_name, prop_schema, prop_name in required_fields))
        body_bva_cases.extend(generate_3point_bva_for_property(prop_name, prop_schema))

    # Query & Path parameter EP + 3-Point BVA across all paths
    parameter_cases: list[dict[str, Any]] = []
    for path_key, path_item in spec.get("paths", {}).items():
        path_level_params = path_item.get("parameters", [])
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in path_item:
                continue
            op = path_item[method]
            all_params = list(path_level_params) + list(op.get("parameters", []))
            for param in all_params:
                pname = param["name"]
                pin = param["in"]
                pschema = resolve_ref(spec, param.get("schema", {}))
                ep = generate_ep_for_property(pname, pschema, bool(param.get("required", False)))
                bva = generate_3point_bva_for_property(pname, pschema)
                for c in ep + bva:
                    c["endpoint"] = path_key
                    c["method"] = method.upper()
                    c["param_in"] = pin
                    c["case_id"] = f"{op.get('operationId', method)}-{pin}-{c['case_id']}"
                    parameter_cases.append(c)

    state_transitions = write_schema.get("x-state-transitions", {})

    return {
        "meta": {
            "spec_file": str(spec_path.as_posix()),
            "spec_title": spec.get("info", {}).get("title"),
            "spec_version": spec.get("info", {}).get("version"),
            "spec_sha256_16": spec_hash,
            "generated_at_utc": iso_utc(anchor_now),
            "counts": {
                "body_ep_cases": len(body_ep_cases),
                "body_bva_cases": len(body_bva_cases),
                "parameter_cases": len(parameter_cases),
                "allowed_transitions": len(state_transitions.get("allowed", [])),
                "disallowed_transitions": len(state_transitions.get("disallowed", [])),
            },
        },
        "constraints_snapshot": constraints_snapshot,
        "baseline_valid_payload": baseline_payload,
        "body_ep_cases": body_ep_cases,
        "body_bva_cases": body_bva_cases,
        "parameter_cases": parameter_cases,
        "state_transitions": state_transitions,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate EP & 3-point BVA API test data from an OpenAPI 3.0 spec.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("openapi/temporary_physical_access_requests.yaml"),
        help="Path to OpenAPI 3.0 YAML/JSON specification.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/team/api/generated_test_data.json"),
        help="Destination path for generated JSON dataset.",
    )
    args = parser.parse_args()

    dataset = generate_dataset(args.spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, indent=2), encoding="utf-8")

    counts = dataset["meta"]["counts"]
    print(f"Generated API test data from {args.spec} (sha256={dataset['meta']['spec_sha256_16']})")
    print(f"  Output: {args.output}")
    print(f"  Body EP cases:         {counts['body_ep_cases']}")
    print(f"  Body 3-Point BVA:      {counts['body_bva_cases']}")
    print(f"  Query/Path param cases:{counts['parameter_cases']}")
    print(f"  State transitions:     {counts['allowed_transitions']} allowed, {counts['disallowed_transitions']} disallowed")


if __name__ == "__main__":
    main()
