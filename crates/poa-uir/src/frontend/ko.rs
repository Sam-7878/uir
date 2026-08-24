use std::collections::BTreeMap;

use super::lexicon::KoreanLexicon;
use crate::{
    DslFrontend, Enforcement, ExecutionContract, ExecutionMode, FailureBehavior, Intent, Language,
    OutputContract, OutputFormat, PolicyConstraint, PolicyLevel, Semantics, Target,
    UirCompileError, UniversalIrDraft, UnsupportedClaimBehavior,
};

#[derive(Default)]
pub struct KoreanFrontend;

impl DslFrontend for KoreanFrontend {
    fn language(&self) -> Language {
        Language::Ko
    }

    fn compile(&self, input: &str) -> Result<UniversalIrDraft, UirCompileError> {
        super::pipeline::compile_typed(input, Language::Ko, &KoreanLexicon)
    }
}

pub(crate) fn build(
    intent: Intent,
    entity: String,
    metric: String,
    year: String,
    input: &str,
) -> Result<UniversalIrDraft, UirCompileError> {
    if intent == Intent::Compare
        && !(input.contains("대비")
            || input.contains("비교")
            || input.to_ascii_lowercase().contains("compare"))
    {
        return Err(UirCompileError::Incomplete("comparison operand".into()));
    }
    let mut parameters = BTreeMap::new();
    parameters.insert("metric".into(), metric.clone());
    parameters.insert("period".into(), year.clone());
    parameters.insert("actor".into(), "research-agent".into());
    let condition = super::condition_parser::parse_condition(input);
    let lowered = input.to_lowercase();
    let enforcement = if input.contains("차단") || lowered.contains("block") {
        Enforcement::BlockExecution
    } else if input.contains("격리") || lowered.contains("quarantine") {
        Enforcement::Quarantine
    } else if input.contains("감축") || lowered.contains("degrade") {
        Enforcement::GracefulDegradation
    } else if input.contains("허용") || lowered.contains("allow") {
        Enforcement::Bypass
    } else {
        Enforcement::Reject
    };
    Ok(UniversalIrDraft {
        semantics: Semantics {
            intent,
            target: Target {
                entity_type: "organization".into(),
                entity_id: entity,
            },
            action: "verify_fact".into(),
            parameters,
            conditions: vec![condition.clone()],
            temporal_scope: Some(year),
        },
        policy_constraints: vec![PolicyConstraint {
            id: "entity-must-exist".into(),
            level: PolicyLevel::L1Domain,
            condition,
            enforcement,
            source: "registry-policy".into(),
        }],
        execution_contract: ExecutionContract {
            required_capabilities: vec!["entity_registry".into(), "verified_fact_lookup".into()],
            required_resources: vec![metric],
            allowed_operations: vec!["verify_fact".into()],
            provenance_requirements: vec!["source_id".into()],
            failure_behavior: FailureBehavior::Reject,
            execution_mode: ExecutionMode::VerifiedOnly,
        },
        output_contract: OutputContract {
            format: OutputFormat::GroundedNaturalLanguage,
            allowed_claim_types: vec!["numeric_fact".into(), "entity_fact".into()],
            provenance_required: true,
            numeric_exactness: true,
            allow_external_inference: false,
            unsupported_claim_behavior: UnsupportedClaimBehavior::Reject,
        },
        domain: "research_finance".into(),
    })
}
