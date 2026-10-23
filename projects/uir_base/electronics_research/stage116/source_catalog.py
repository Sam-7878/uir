"""Runtime catalog producer, separately coded from the scorer extraction.

No gold/expected labels, interpreter or reference parser imports are permitted.
Only JSON/TOML wire parsing standards are shared with the reference scorer.
"""
import json
import tomllib


def usd_cents(raw):
    if not isinstance(raw, str):
        raise ValueError("USD_SOURCE_NOT_TEXT")
    negative = raw.startswith("-")
    text = raw[1:] if negative else raw
    dollars, _, fraction = text.partition(".")
    if not dollars.isascii() or not dollars.isdigit() or len(fraction) > 2 or (fraction and not fraction.isdigit()):
        raise ValueError("NO_ROUNDING_OR_NONDECIMAL_SOURCE_ALLOWED")
    result = int(dollars) * 100 + int((fraction + "00")[:2])
    return str(-result if negative else result)


def build_catalog(treasury_path, cargo_path):
    facts = []
    def add(entity, metric, period, unit, value, pointer, family):
        facts.append({"entity": entity, "metric": metric, "period": period, "unit": unit, "value": value,
                      "provenance": family + pointer, "status": "current", "visibility": "public"})
    table = json.loads(treasury_path.read_bytes())["data"]
    for index in range(len(table)):
        for metric in ("intragov_hold_amt", "tot_pub_debt_out_amt", "debt_held_public_amt"):
            add("US_TREASURY", metric, table[index]["record_date"], "USD_CENT", usd_cents(table[index][metric]),
                f"/data/{index}/{metric}", "US-Treasury:DebtToPenny")
    config = tomllib.loads(cargo_path.read_text())
    tables = [("package", config["package"], "/package"), ("workspace", config["workspace"]["package"], "/workspace/package")]
    for table_name, data, pointer in tables:
        for key in ("rust-version", "version", "edition"):
            if key not in data or not isinstance(data[key], str):
                continue
            if key == "edition":
                add("CARGO", table_name + "_edition", "snapshot", "YEAR", str(int(data[key])), pointer + "/edition", "GitHub:rust-lang/cargo")
            else:
                prefix = table_name + ("_rust_" if key == "rust-version" else "_version_")
                pieces = data[key].split(".")
                for i in range(len(pieces)):
                    component = ("major", "minor", "patch")[i]
                    add("CARGO", prefix + component, "snapshot", "COUNT", str(int(pieces[i])), pointer + "/" + key + "#" + component, "GitHub:rust-lang/cargo")
    facts.sort(key=lambda f: (f["entity"], f["metric"], f["period"], f["unit"]))
    for index, fact in enumerate(facts):
        fact["id"] = f"FACT-{index:03}"
    return facts
