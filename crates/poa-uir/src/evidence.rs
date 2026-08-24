use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::{Language, OutputValidation, PolicyDecision, UniversalIr, semantic_digest, uir_digest};

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct StageLatenciesUs {
    pub dsl_compile_us: u64,
    pub uir_validate_us: u64,
    pub policy_eval_us: u64,
    pub aaco_us: u64,
    pub executor_us: u64,
    pub slm_us: u64,
    pub output_validate_us: u64,
    pub canonicalization_us: u64,
    pub digest_us: u64,
    pub total_us: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UirAuditEvidence {
    pub request_id: String,
    pub uir_digest: String,
    pub semantic_digest: String,
    pub policy_digest: String,
    pub source_language: Language,
    pub compile_result: String,
    pub validation_result: String,
    pub policy_decision: PolicyDecision,
    pub aaco_outcome: String,
    pub reason_code: Option<String>,
    pub stage_latencies_us: StageLatenciesUs,
    pub verified_fact_count: usize,
    pub generated_claim_count: usize,
    pub supported_claim_count: usize,
    pub unsupported_claim_count: usize,
    pub output_validation_result: String,
    pub attributes: BTreeMap<String, String>,
}

pub struct EvidenceInputs<'a> {
    pub policy_digest: String,
    pub policy_decision: PolicyDecision,
    pub aaco_outcome: String,
    pub reason_code: Option<String>,
    pub stage_latencies_us: StageLatenciesUs,
    pub verified_fact_count: usize,
    pub output_validation: Option<&'a OutputValidation>,
}

impl UirAuditEvidence {
    pub fn new(uir: &UniversalIr, inputs: EvidenceInputs<'_>) -> Result<Self, crate::UirError> {
        let output = inputs.output_validation;
        Ok(Self {
            request_id: uir.metadata.request_id.clone(),
            uir_digest: uir_digest(uir)?,
            semantic_digest: semantic_digest(uir)?,
            policy_digest: inputs.policy_digest,
            source_language: uir.metadata.source_language.clone(),
            compile_result: "success".into(),
            validation_result: "valid".into(),
            policy_decision: inputs.policy_decision,
            aaco_outcome: inputs.aaco_outcome,
            reason_code: inputs.reason_code,
            stage_latencies_us: inputs.stage_latencies_us,
            verified_fact_count: inputs.verified_fact_count,
            generated_claim_count: output.map_or(0, |item| item.generated_claim_count),
            supported_claim_count: output.map_or(0, |item| item.supported_claim_count),
            unsupported_claim_count: output.map_or(0, |item| item.unsupported_claim_count),
            output_validation_result: output
                .map_or("not_invoked", |item| {
                    if item.accepted {
                        "accepted"
                    } else {
                        "rejected"
                    }
                })
                .into(),
            attributes: BTreeMap::new(),
        })
    }
}
