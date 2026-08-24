use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::Condition;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Language {
    Ko,
    En,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Intent {
    Summarize,
    Extract,
    Analyze,
    Compare,
    CauseTrace,
    Verify,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PolicyLevel {
    L0System,
    L1Domain,
    L2Enterprise,
    L3Preference,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Enforcement {
    BlockExecution,
    Reject,
    GracefulDegradation,
    Quarantine,
    Bypass,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ExecutionMode {
    VerifiedOnly,
    DryRun,
    Standard,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum FailureBehavior {
    Reject,
    Degrade,
    Quarantine,
    Abort,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OutputFormat {
    StructuredJson,
    GroundedNaturalLanguage,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum UnsupportedClaimBehavior {
    Reject,
    Remove,
    Flag,
    FilterAndRender,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Metadata {
    pub uir_version: String,
    pub request_id: String,
    pub source_language: Language,
    pub source_hash: String,
    pub compiler_version: String,
    pub domain: String,
    pub created_at: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Target {
    pub entity_type: String,
    pub entity_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Semantics {
    pub intent: Intent,
    pub target: Target,
    pub action: String,
    pub parameters: BTreeMap<String, String>,
    pub conditions: Vec<Condition>,
    pub temporal_scope: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PolicyConstraint {
    pub id: String,
    pub level: PolicyLevel,
    pub condition: Condition,
    pub enforcement: Enforcement,
    pub source: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExecutionContract {
    pub required_capabilities: Vec<String>,
    pub required_resources: Vec<String>,
    pub allowed_operations: Vec<String>,
    pub provenance_requirements: Vec<String>,
    pub failure_behavior: FailureBehavior,
    pub execution_mode: ExecutionMode,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OutputContract {
    pub format: OutputFormat,
    pub allowed_claim_types: Vec<String>,
    pub provenance_required: bool,
    pub numeric_exactness: bool,
    pub allow_external_inference: bool,
    pub unsupported_claim_behavior: UnsupportedClaimBehavior,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UniversalIr {
    pub version: String,
    pub metadata: Metadata,
    pub semantics: Semantics,
    pub policy_constraints: Vec<PolicyConstraint>,
    pub execution_contract: ExecutionContract,
    pub output_contract: OutputContract,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UniversalIrDraft {
    pub semantics: Semantics,
    pub policy_constraints: Vec<PolicyConstraint>,
    pub execution_contract: ExecutionContract,
    pub output_contract: OutputContract,
    pub domain: String,
}
