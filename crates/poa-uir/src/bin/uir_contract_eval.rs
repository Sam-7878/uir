//! Independent S1 JSON-line interpreter. Only canonical serialization is shared;
//! policy, selection, provenance and derivation decisions are implemented here.
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeSet, HashMap, HashSet};
use std::io::{self, BufRead};

fn digest(value: &Value) -> Result<String, String> {
    let bytes = poa_protocol::canonicalize_value(value).map_err(|e| e.to_string())?;
    Ok(hex::encode(Sha256::digest(bytes)))
}

fn string<'a>(value: &'a Value, key: &str) -> Result<&'a str, String> {
    value[key].as_str().ok_or_else(|| format!("STRING_{key}"))
}

fn exact_keys(value: &Value, keys: &[&str]) -> bool {
    value
        .as_object()
        .is_some_and(|map| map.len() == keys.len() && keys.iter().all(|key| map.contains_key(*key)))
}

fn forbidden(value: &Value) -> bool {
    match value {
        Value::Object(map) => map.iter().any(|(k, v)| {
            [
                "expected_ids",
                "expected_state",
                "gold",
                "gold_program",
                "exe_ans",
                "expected_claims",
            ]
            .contains(&k.as_str())
                || forbidden(v)
        }),
        Value::Array(items) => items.iter().any(forbidden),
        _ => false,
    }
}

fn outcome(state: &str, ids: BTreeSet<String>) -> Value {
    json!({"state": state, "fact_ids": ids.into_iter().collect::<Vec<_>>()})
}

fn supported(
    id: &str,
    facts: &HashMap<String, Value>,
    query: &Value,
    trusted: &Value,
    visiting: &mut HashSet<String>,
    completed: &mut HashSet<String>,
) -> Result<bool, String> {
    if visiting.contains(id) {
        return Err("CYCLE".into());
    }
    if completed.contains(id) {
        return Ok(true);
    }
    let Some(fact) = facts.get(id) else {
        return Ok(false);
    };
    if fact["status"] != "current" || fact["visibility"] != "public" {
        return Ok(false);
    }
    if fact["entity"] != query["entity"] || fact["period"] != query["period"] {
        return Err("DEPENDENCY_SCOPE".into());
    }
    if !trusted
        .as_array()
        .ok_or("TRUSTED_PROVENANCE")?
        .contains(&fact["provenance"])
    {
        return Err("PROVENANCE".into());
    }
    let raw = string(fact, "value")?;
    if raw.is_empty()
        || !raw
            .trim_start_matches('-')
            .bytes()
            .all(|b| b.is_ascii_digit())
    {
        return Err("INTEGER_FACT".into());
    }
    let value = raw.parse::<i128>().map_err(|_| "INTEGER_RANGE")?;
    visiting.insert(id.into());
    let deps = match fact.get("dependencies") {
        Some(items) => items.as_array().ok_or("DEPENDENCIES")?.clone(),
        None => vec![],
    };
    for dep in &deps {
        if !supported(
            dep.as_str().ok_or("DEP_ID")?,
            facts,
            query,
            trusted,
            visiting,
            completed,
        )? {
            visiting.remove(id);
            return Ok(false);
        }
    }
    if let Some(operation) = fact.get("operation") {
        if operation != "PERCENT_DIV" || deps.len() != 2 || fact["unit"] != "percent" {
            return Err("DERIVATION".into());
        }
        let a = facts
            .get(deps[0].as_str().ok_or("DEP_ID")?)
            .ok_or("OPERAND")?;
        let b = facts
            .get(deps[1].as_str().ok_or("DEP_ID")?)
            .ok_or("OPERAND")?;
        if a["unit"] != b["unit"] || (a["unit"] != "USD" && a["unit"] != "EUR") {
            return Err("OPERAND_UNIT".into());
        }
        let numerator = string(a, "value")?
            .parse::<i128>()
            .map_err(|_| "OPERAND_INT")?;
        let denominator = string(b, "value")?
            .parse::<i128>()
            .map_err(|_| "OPERAND_INT")?;
        let scaled = numerator.checked_mul(100).ok_or("OVERFLOW")?;
        if denominator == 0
            || scaled.checked_rem(denominator) != Some(0)
            || scaled.checked_div(denominator) != Some(value)
        {
            return Err("DERIVATION_VALUE".into());
        }
    } else if !deps.is_empty() {
        return Err("UNDEFINED_DEPENDENCY".into());
    }
    visiting.remove(id);
    completed.insert(id.into());
    Ok(true)
}

fn decide(packet: &Value) -> Result<Value, String> {
    if forbidden(packet) {
        return Err("GOLD".into());
    }
    let ir = &packet["artifact"];
    if !exact_keys(
        ir,
        &[
            "metadata",
            "semantics",
            "policy_constraints",
            "execution_contract",
            "output_contract",
            "semantic_digest",
        ],
    ) {
        return Err("SECTIONS".into());
    }
    let bound = json!({"semantics": ir["semantics"], "policy_constraints": ir["policy_constraints"],
                       "execution_contract": ir["execution_contract"], "output_contract": ir["output_contract"]});
    if digest(&bound)? != string(ir, "semantic_digest")? {
        return Err("DIGEST".into());
    }
    let query = &ir["semantics"];
    let policy = &ir["policy_constraints"];
    let execution = &ir["execution_contract"];
    if execution["version"] != "uir-query-contract-S1"
        || !exact_keys(query, &["entity", "metric", "period", "unit", "predicate"])
        || ir["output_contract"]
            != json!({"language":"CLOSED_FACT_LINES_S1","partial":true,"dependency_closure":true})
        || policy["allowed_operations"] != json!(["read", "PERCENT_DIV"])
        || (policy["action"] != "read" && policy["action"] != "write")
    {
        return Err("SCHEMA_VERSION".into());
    }
    let authority = &packet["authority"];
    if policy["version"] != authority["version"]
        || execution["evidence_version"] != packet["current_evidence_version"]
    {
        return Err("SNAPSHOT".into());
    }
    let evidence = json!({"version":execution["evidence_version"], "facts":execution["facts"],
                          "trusted_provenance":execution["trusted_provenance"]});
    if digest(&evidence)? != string(packet, "current_evidence_sha256")? {
        return Err("ROOT".into());
    }
    let pred = &query["predicate"];
    if !pred.is_null() {
        if !exact_keys(pred, &["op", "field", "value"])
            || pred["op"] != "EQ_BOOL"
            || pred["value"].as_bool().is_none()
            || pred["field"].as_str().is_none()
        {
            return Ok(outcome("CLARIFICATION", BTreeSet::new()));
        }
        let observed = packet["context"][pred["field"].as_str().ok_or("FIELD")?].as_bool();
        if observed.is_none() {
            return Ok(outcome("CLARIFICATION", BTreeSet::new()));
        }
        if observed != pred["value"].as_bool() {
            return Ok(outcome("DENY", BTreeSet::new()));
        }
    }
    let decision = string(authority, "decision")?;
    if decision == "DENY" {
        return Ok(outcome("DENY", BTreeSet::new()));
    }
    if decision == "APPROVAL" && authority["approved"] != true {
        return Ok(outcome("APPROVAL_PENDING", BTreeSet::new()));
    }
    if decision == "READ_ONLY" && policy["action"] == "write" {
        return Ok(outcome("READ_ONLY", BTreeSet::new()));
    }
    if !["ALLOW", "APPROVAL", "READ_ONLY"].contains(&decision) {
        return Err("POLICY".into());
    }
    if !policy["allowed_operations"]
        .as_array()
        .ok_or("OPERATIONS")?
        .contains(&policy["action"])
    {
        return Ok(outcome("DENY", BTreeSet::new()));
    }
    let rows = execution["facts"].as_array().ok_or("FACTS")?;
    let mut facts = HashMap::new();
    for fact in rows {
        if facts
            .insert(string(fact, "id")?.to_string(), fact.clone())
            .is_some()
        {
            return Err("DUPLICATE_ID".into());
        }
    }
    let eligible: Vec<&Value> = rows
        .iter()
        .filter(|f| {
            f["entity"] == query["entity"]
                && f["metric"] == query["metric"]
                && f["period"] == query["period"]
                && f["unit"] == query["unit"]
                && f["status"] == "current"
                && f["visibility"] == "public"
        })
        .collect();
    let values: HashSet<&str> = eligible
        .iter()
        .map(|f| string(f, "value"))
        .collect::<Result<_, _>>()?;
    if values.len() > 1 {
        return Err("CONFLICT".into());
    }
    let mut ids = BTreeSet::new();
    let mut visiting = HashSet::new();
    let mut completed = HashSet::new();
    for fact in eligible {
        let id = string(fact, "id")?;
        if supported(
            id,
            &facts,
            query,
            &execution["trusted_provenance"],
            &mut visiting,
            &mut completed,
        )? {
            ids.insert(id.into());
        }
    }
    Ok(outcome(
        if ids.is_empty() {
            "NO_VERIFIED_ANSWER"
        } else {
            "FULL_VERIFIED_ANSWER"
        },
        ids,
    ))
}

fn main() {
    for line in io::stdin().lock().lines() {
        let result = line
            .ok()
            .and_then(|line| serde_json::from_str::<Value>(&line).ok())
            .and_then(|packet| decide(&packet).ok())
            .unwrap_or_else(|| outcome("QUARANTINE", BTreeSet::new()));
        println!("{result}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_sections_are_not_accepted() {
        assert!(decide(&json!({"artifact": {}})).is_err());
    }
    #[test]
    fn evaluator_gold_is_not_runtime_input() {
        assert!(forbidden(&json!({"nested": {"expected_ids": []}})));
    }
}
