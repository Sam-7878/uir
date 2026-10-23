"""Scorer-only reference: parses original source bytes, never runtime decisions.

Machine gold is exact for the declared scalar extraction/CNL, NOT human NL truth.
This code is deliberately not imported by the runtime worker.
"""
from decimal import Decimal
import json
import tomllib


def source_values(treasury_path, cargo_path):
    records = []
    for row_index, row in enumerate(json.loads(treasury_path.read_text())["data"]):
        for field in ("debt_held_public_amt", "intragov_hold_amt", "tot_pub_debt_out_amt"):
            cents = Decimal(row[field]) * Decimal(100)
            if not cents.is_finite() or cents != cents.to_integral_value():
                raise ValueError("SOURCE_REQUIRES_UNDECLARED_ROUNDING")
            records.append({"entity": "US_TREASURY", "metric": field, "period": row["record_date"],
                            "unit": "USD_CENT", "value": str(int(cents)), "source_pointer": f"/data/{row_index}/{field}"})
    manifest = tomllib.loads(cargo_path.read_text())
    for scope, data in (("package", manifest["package"]), ("workspace", manifest["workspace"]["package"])):
        pointer_scope = "workspace/package" if scope == "workspace" else scope
        if "rust-version" in data:
            for component, value in zip(("major", "minor", "patch"), data["rust-version"].split(".")):
                records.append({"entity": "CARGO", "metric": f"{scope}_rust_{component}", "period": "snapshot",
                                "unit": "COUNT", "value": str(int(value)), "source_pointer": f"/{pointer_scope}/rust-version#{component}"})
        if isinstance(data.get("edition"), str):
            records.append({"entity": "CARGO", "metric": f"{scope}_edition", "period": "snapshot", "unit": "YEAR",
                            "value": str(int(data["edition"])), "source_pointer": f"/{pointer_scope}/edition"})
    for component, value in zip(("major", "minor", "patch"), manifest["package"]["version"].split(".")):
        records.append({"entity": "CARGO", "metric": "package_version_" + component, "period": "snapshot", "unit": "COUNT",
                        "value": str(int(value)), "source_pointer": "/package/version#" + component})
    return records


def interpret_raw_reference(raw):
    # A separately coded string parser, not the runtime regex/parser/selector.
    if raw.startswith("At ") and raw.endswith("."):
        period, tail = raw[3:-1].split(", return ", 1)
        metric, tail = tail.split(" for ", 1)
        entity, unit = tail.split(" in ", 1)
    else:
        period, tail = raw.split(" 기준 ", 1)
        entity, tail = tail.split("의 ", 1)
        metric, tail = tail.split(" 항목을 ", 1)
        unit = tail.removesuffix(" 단위로 응답하세요.")
        if not raw.endswith(" 단위로 응답하세요."):
            raise ValueError("UNSUPPORTED_REFERENCE_CNL")
    return dict(entity=entity, metric=metric, period=period, unit=unit)


def reference_gold(raw, originals):
    query = interpret_raw_reference(raw)
    matches = [r for r in originals if all(r[k] == query[k] for k in query)]
    if len(matches) != 1:
        raise ValueError("REFERENCE_NOT_UNIQUE")
    return {"semantics": query, "source_pointer": matches[0]["source_pointer"], "value": matches[0]["value"],
            "truth_scope": "SOURCE_SCALAR_AND_DECLARED_CNL_MACHINE_GOLD_NOT_HUMAN"}
