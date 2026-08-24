use std::{
    collections::BTreeSet,
    env,
    fs::File,
    io::{BufRead, BufReader, BufWriter, Write},
    time::Instant,
};

use poa_protocol::{
    DataConstraints, DeploymentMode, EffectivePolicy, FailurePolicy, OperationPolicy, OsBackend,
    ProcessConstraints,
};
use poa_uir::*;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Case {
    case_id: String,
    language: String,
    category: String,
    input: String,
    expected_outcome: String,
    expected_policy_decision: String,
    #[serde(default)]
    expected_semantics: serde_json::Value,
    #[serde(default)]
    expected_conditions: serde_json::Value,
    #[serde(default = "yes")]
    entity_valid: bool,
    #[serde(default = "yes")]
    policy_valid: bool,
    #[serde(default)]
    output_violation: bool,
}
fn yes() -> bool {
    true
}

#[derive(Serialize)]
struct Record {
    case_id: String,
    language: String,
    category: String,
    expected_outcome: String,
    actual_outcome: String,
    expected_policy_decision: String,
    actual_policy_decision: String,
    correct: bool,
    semantic_digest: Option<String>,
    uir_digest: Option<String>,
    reason_code: Option<String>,
    renderer_invocations: u64,
    verified_fact_count: usize,
    generated_claim_count: usize,
    supported_claim_count: usize,
    unsupported_claim_count: usize,
    output_validation_result: String,
    serialized_bytes: usize,
    stage_latencies_us: StageLatenciesUs,
    exact_structural_match: bool,
    semantic_match: bool,
    condition_ast_exact_match: bool,
    resolution_status: String,
    actual_semantics: serde_json::Value,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args().collect();
    if args.len() != 3 {
        return Err("usage: uir-eval DATASET.jsonl OUTPUT.jsonl".into());
    }
    let reader = BufReader::new(File::open(&args[1])?);
    let mut writer = BufWriter::new(File::create(&args[2])?);
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let case: Case = serde_json::from_str(&line)?;
        let record = execute(case);
        serde_json::to_writer(&mut writer, &record)?;
        writer.write_all(b"\n")?;
    }
    Ok(())
}

fn execute(case: Case) -> Record {
    let total = Instant::now();
    let mut latency = StageLatenciesUs::default();
    let started = Instant::now();
    let options = CompileOptions {
        request_id: case.case_id.clone(),
        created_at: "2026-08-07T00:00:00Z".into(),
        compiler_version: env!("CARGO_PKG_VERSION").into(),
    };
    let compiled = compile_input(&case.input, &options);
    latency.dsl_compile_us = micros(started);
    let Ok(uir) = compiled else {
        let resolution = resolve_input(&case.input, &options);
        let outcome = if resolution.status == SemanticResolutionStatus::NeedsClarification {
            "NEEDS_CLARIFICATION"
        } else {
            "REJECT"
        };
        return terminal(
            case,
            outcome,
            "REJECT",
            Some("UIR_SCHEMA_INVALID".into()),
            format!("{:?}", resolution.status).to_uppercase(),
            latency,
            total,
        );
    };
    let actual_semantics = semantic_projection(&uir);
    let semantic_match =
        case.expected_semantics.is_null() || case.expected_semantics == actual_semantics;
    let actual_conditions = serde_json::to_value(&uir.semantics.conditions).unwrap_or_default();
    let condition_ast_exact_match =
        case.expected_conditions.is_null() || case.expected_conditions == actual_conditions;
    let serialized_bytes = serde_json::to_vec(&uir).map_or(0, |bytes| bytes.len());
    let started = Instant::now();
    let validated = validate(uir.clone());
    latency.uir_validate_us = micros(started);
    let Ok(validated) = validated else {
        return terminal(
            case,
            "REJECT",
            "REJECT",
            Some("UIR_SEMANTIC_INVALID".into()),
            "INVALID".into(),
            latency,
            total,
        );
    };
    let started = Instant::now();
    let canonical = canonicalize_uir(&uir).ok();
    latency.canonicalization_us = micros(started);
    let started = Instant::now();
    let full_digest = uir_digest(&uir).ok();
    let semantic = semantic_digest(&uir).ok();
    latency.digest_us = micros(started);
    let mut entities = BTreeSet::new();
    if case.entity_valid {
        entities.insert(uir.semantics.target.entity_id.clone());
    }
    let actor = if case.policy_valid {
        "research-agent"
    } else {
        "unauthorized-agent"
    };
    let started = Instant::now();
    let policy_result = evaluate_policy(
        &validated,
        &policy(),
        &RuntimeContext {
            actor: actor.into(),
            verified_entities: entities,
            risk_threshold_exceeded: false,
        },
    )
    .expect("policy serialization");
    latency.policy_eval_us = micros(started);
    let started = Instant::now();
    let outcome = execute_aaco(&validated, &policy_result);
    latency.aaco_us = micros(started);
    let actual_outcome = outcome.label().to_uppercase();
    let mut renderer = MockRenderer::new(case.output_violation);
    let (facts, output_validation) = if matches!(outcome, poa_core::TransitionOutcome::Commit) {
        let started = Instant::now();
        let facts = FixtureExecutor.execute(&validated).unwrap_or_default();
        latency.executor_us = micros(started);
        let started = Instant::now();
        let output = renderer.render(&validated, &facts).expect("mock rendering");
        latency.slm_us = micros(started);
        let started = Instant::now();
        let validation = validate_output(&validated, &facts, &output);
        latency.output_validate_us = micros(started);
        (facts, Some(validation))
    } else {
        (VerifiedFactSet::default(), None)
    };
    let final_outcome = if output_validation
        .as_ref()
        .is_some_and(|value| !value.accepted)
    {
        "REJECT".into()
    } else {
        actual_outcome
    };
    latency.total_us = micros(total);
    let decision = format!("{:?}", policy_result.decision).to_uppercase();
    Record {
        correct: final_outcome == case.expected_outcome,
        case_id: case.case_id,
        language: case.language,
        category: case.category,
        expected_outcome: case.expected_outcome,
        actual_outcome: final_outcome,
        expected_policy_decision: case.expected_policy_decision,
        actual_policy_decision: decision,
        semantic_digest: semantic,
        uir_digest: full_digest,
        reason_code: policy_result.reason_code.map(str::to_owned).or_else(|| {
            output_validation
                .as_ref()
                .filter(|value| !value.accepted)
                .map(|_| "UIR_OUTPUT_CONTRACT_VIOLATION".into())
        }),
        renderer_invocations: renderer.invocation_count(),
        verified_fact_count: facts.0.len(),
        generated_claim_count: output_validation
            .as_ref()
            .map_or(0, |value| value.generated_claim_count),
        supported_claim_count: output_validation
            .as_ref()
            .map_or(0, |value| value.supported_claim_count),
        unsupported_claim_count: output_validation
            .as_ref()
            .map_or(0, |value| value.unsupported_claim_count),
        output_validation_result: output_validation
            .as_ref()
            .map_or("not_invoked", |value| {
                if value.accepted {
                    "accepted"
                } else {
                    "rejected"
                }
            })
            .into(),
        serialized_bytes: canonical.map_or(serialized_bytes, |value| value.len()),
        stage_latencies_us: latency,
        exact_structural_match: semantic_match && condition_ast_exact_match,
        semantic_match,
        condition_ast_exact_match,
        resolution_status: "RESOLVED".into(),
        actual_semantics,
    }
}

fn terminal(
    case: Case,
    outcome: &str,
    decision: &str,
    reason: Option<String>,
    resolution_status: String,
    mut latency: StageLatenciesUs,
    total: Instant,
) -> Record {
    latency.total_us = micros(total);
    Record {
        correct: outcome == case.expected_outcome,
        case_id: case.case_id,
        language: case.language,
        category: case.category,
        expected_outcome: case.expected_outcome,
        actual_outcome: outcome.into(),
        expected_policy_decision: case.expected_policy_decision,
        actual_policy_decision: decision.into(),
        semantic_digest: None,
        uir_digest: None,
        reason_code: reason,
        renderer_invocations: 0,
        verified_fact_count: 0,
        generated_claim_count: 0,
        supported_claim_count: 0,
        unsupported_claim_count: 0,
        output_validation_result: "not_invoked".into(),
        serialized_bytes: 0,
        stage_latencies_us: latency,
        exact_structural_match: case.expected_semantics.is_null()
            && case.expected_conditions.is_null(),
        semantic_match: case.expected_semantics.is_null(),
        condition_ast_exact_match: case.expected_conditions.is_null(),
        resolution_status,
        actual_semantics: serde_json::Value::Null,
    }
}

fn micros(start: Instant) -> u64 {
    u64::try_from(start.elapsed().as_micros()).unwrap_or(u64::MAX)
}

fn semantic_projection(uir: &UniversalIr) -> serde_json::Value {
    serde_json::json!({"intent": uir.semantics.intent, "target": uir.semantics.target.entity_id, "action": uir.semantics.action, "metric": uir.semantics.parameters.get("metric"), "period": uir.semantics.parameters.get("period")})
}

fn policy() -> EffectivePolicy {
    EffectivePolicy {
        schema: "https://schema.hete.io/poa/v1.json".into(),
        protocol_id: "uir.evaluation".into(),
        version: "1.0.0".into(),
        extends: None,
        mode: DeploymentMode::Development,
        operations: vec![OperationPolicy {
            name: "verify_fact".into(),
            allowed_actors: vec!["research-agent".into()],
            required_context: vec!["policy_digest".into()],
        }],
        process_constraints: ProcessConstraints {
            os_backend: OsBackend::Noop,
            pledge_promises: vec![],
            unveil_paths: vec![],
            lock_after_initialization: false,
        },
        data_constraints: DataConstraints {
            input_schema: "protocol/schemas/uir.schema.json".into(),
            maximum_message_bytes: 65_536,
            canonical_encoding: "JCS".into(),
            maximum_nesting_depth: 32,
        },
        failure_policy: FailurePolicy {
            invalid_request: "reject".into(),
            policy_violation: "reject".into(),
            repeated_violation: "quarantine".into(),
            internal_error: "abort".into(),
            quarantine_threshold: 3,
        },
        network_policy: None,
        risk_evidence: None,
        privilege_expansion: None,
    }
}
