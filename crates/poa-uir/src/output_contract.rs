use std::collections::BTreeMap;
use std::io::Write;
use std::process::{Command, Stdio};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::{UniversalIr, UnsupportedClaimBehavior, ValidatedUir};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VerifiedFact {
    pub fact_id: String,
    pub claim_type: String,
    pub key: String,
    pub value: String,
    pub provenance: String,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct VerifiedFactSet(pub Vec<VerifiedFact>);

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GeneratedClaim {
    pub claim_type: String,
    pub key: String,
    pub value: String,
    pub provenance: Option<String>,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GeneratedOutput {
    pub text: String,
    pub claims: Vec<GeneratedClaim>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OutputValidation {
    pub accepted: bool,
    pub generated_claim_count: usize,
    pub supported_claim_count: usize,
    pub unsupported_claim_count: usize,
    pub violations: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EnforcedOutput {
    pub accepted: bool,
    pub complete_rejection: bool,
    pub text: String,
    pub claims: Vec<GeneratedClaim>,
    pub validation: OutputValidation,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VerifiedNumericSlot {
    pub key: String,
    /// Kept as source text: no floating-point conversion or model regeneration.
    pub exact_value: String,
    pub provenance: String,
    pub source_digest: String,
}

pub fn bind_verified_numeric_slots(slots: &[VerifiedNumericSlot]) -> GeneratedOutput {
    let claims = slots
        .iter()
        .map(|slot| GeneratedClaim {
            claim_type: "numeric_fact".into(),
            key: slot.key.clone(),
            value: slot.exact_value.clone(),
            provenance: Some(format!("{}#sha256:{}", slot.provenance, slot.source_digest)),
        })
        .collect::<Vec<_>>();
    GeneratedOutput {
        text: render_supported_claims(&claims),
        claims,
    }
}

fn supported_claims(facts: &VerifiedFactSet, output: &GeneratedOutput) -> Vec<GeneratedClaim> {
    output
        .claims
        .iter()
        .filter(|claim| {
            facts.0.iter().any(|fact| {
                fact.claim_type == claim.claim_type
                    && fact.key == claim.key
                    && fact.value == claim.value
                    && claim.provenance.as_deref() == Some(fact.provenance.as_str())
            })
        })
        .cloned()
        .collect()
}

fn render_supported_claims(claims: &[GeneratedClaim]) -> String {
    claims
        .iter()
        .map(|claim| {
            format!(
                "{}={} [{}]",
                claim.key,
                claim.value,
                claim.provenance.as_deref().unwrap_or("verified")
            )
        })
        .collect::<Vec<_>>()
        .join("; ")
}

/// Enforces the output contract after generation. FILTER_AND_RENDER discards the
/// model prose and deterministically renders only claims matched to verified facts.
pub fn enforce_output_contract(
    uir: &ValidatedUir,
    facts: &VerifiedFactSet,
    output: &GeneratedOutput,
) -> EnforcedOutput {
    let validation = validate_output(uir, facts, output);
    let supported = supported_claims(facts, output);
    let behavior = &uir.as_uir().output_contract.unsupported_claim_behavior;
    let complete_rejection = !validation.accepted
        || (matches!(behavior, UnsupportedClaimBehavior::FilterAndRender) && supported.is_empty());
    let claims = match behavior {
        UnsupportedClaimBehavior::Reject if validation.unsupported_claim_count > 0 => Vec::new(),
        UnsupportedClaimBehavior::Remove | UnsupportedClaimBehavior::FilterAndRender => supported,
        UnsupportedClaimBehavior::Reject | UnsupportedClaimBehavior::Flag => output.claims.clone(),
    };
    let text = if complete_rejection {
        "NO_VERIFIED_ANSWER".into()
    } else if matches!(
        behavior,
        UnsupportedClaimBehavior::Remove | UnsupportedClaimBehavior::FilterAndRender
    ) {
        render_supported_claims(&claims)
    } else {
        output.text.clone()
    };
    EnforcedOutput {
        accepted: !complete_rejection,
        complete_rejection,
        text,
        claims,
        validation,
    }
}

pub fn validate_output(
    uir: &ValidatedUir,
    facts: &VerifiedFactSet,
    output: &GeneratedOutput,
) -> OutputValidation {
    let contract = &uir.as_uir().output_contract;
    let index: BTreeMap<_, _> = facts
        .0
        .iter()
        .map(|fact| {
            (
                (
                    fact.claim_type.as_str(),
                    fact.key.as_str(),
                    fact.value.as_str(),
                ),
                fact,
            )
        })
        .collect();
    let mut supported = 0;
    let mut violations = Vec::new();
    for claim in &output.claims {
        if !contract.allowed_claim_types.contains(&claim.claim_type) {
            violations.push(format!("claim type not allowed: {}", claim.claim_type));
            continue;
        }
        let fact = index.get(&(
            claim.claim_type.as_str(),
            claim.key.as_str(),
            claim.value.as_str(),
        ));
        match fact {
            Some(fact)
                if !contract.provenance_required
                    || claim.provenance.as_deref() == Some(fact.provenance.as_str()) =>
            {
                supported += 1
            }
            Some(_) => violations.push(format!("provenance mismatch: {}", claim.key)),
            None => violations.push(format!("unsupported claim: {}", claim.key)),
        }
    }
    let unsupported = output.claims.len().saturating_sub(supported);
    let accepted = unsupported == 0
        || matches!(
            contract.unsupported_claim_behavior,
            UnsupportedClaimBehavior::Remove
                | UnsupportedClaimBehavior::Flag
                | UnsupportedClaimBehavior::FilterAndRender
        );
    OutputValidation {
        accepted,
        generated_claim_count: output.claims.len(),
        supported_claim_count: supported,
        unsupported_claim_count: unsupported,
        violations,
    }
}

pub trait Renderer {
    fn render(
        &mut self,
        uir: &ValidatedUir,
        facts: &VerifiedFactSet,
    ) -> Result<GeneratedOutput, RenderError>;
    fn invocation_count(&self) -> u64;
}

#[derive(Debug, Error)]
pub enum RenderError {
    #[error("renderer I/O failed: {0}")]
    Io(#[from] std::io::Error),
    #[error("renderer subprocess failed: {0}")]
    Subprocess(String),
    #[error("renderer protocol failed: {0}")]
    Protocol(#[from] serde_json::Error),
}

#[derive(Default)]
pub struct MockRenderer {
    invocations: u64,
    pub inject_unsupported: bool,
}

impl MockRenderer {
    pub fn new(inject_unsupported: bool) -> Self {
        Self {
            invocations: 0,
            inject_unsupported,
        }
    }
}

impl Renderer for MockRenderer {
    fn render(
        &mut self,
        _: &ValidatedUir,
        facts: &VerifiedFactSet,
    ) -> Result<GeneratedOutput, RenderError> {
        self.invocations += 1;
        let mut claims: Vec<_> = facts
            .0
            .iter()
            .map(|fact| GeneratedClaim {
                claim_type: fact.claim_type.clone(),
                key: fact.key.clone(),
                value: fact.value.clone(),
                provenance: Some(fact.provenance.clone()),
            })
            .collect();
        if self.inject_unsupported {
            claims.push(GeneratedClaim {
                claim_type: "numeric_fact".into(),
                key: "unsupported".into(),
                value: "999".into(),
                provenance: None,
            });
        }
        Ok(GeneratedOutput {
            text: "verified facts rendered".into(),
            claims,
        })
    }
    fn invocation_count(&self) -> u64 {
        self.invocations
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LocalSlmRendererConfig {
    pub python_executable: String,
    pub bridge_script: String,
    pub model: String,
    pub temperature: f64,
    pub top_p: f64,
    pub top_k: u64,
    pub max_new_tokens: u64,
    pub repetition_penalty: f64,
    pub seed: u64,
}

pub struct LocalSlmRenderer {
    config: LocalSlmRendererConfig,
    invocations: u64,
}

#[derive(Serialize)]
struct LocalSlmRequest<'a> {
    model: &'a str,
    uir: &'a UniversalIr,
    facts: &'a VerifiedFactSet,
    temperature: f64,
    top_p: f64,
    top_k: u64,
    max_new_tokens: u64,
    repetition_penalty: f64,
    seed: u64,
}

impl LocalSlmRenderer {
    pub fn new(config: LocalSlmRendererConfig) -> Self {
        Self {
            config,
            invocations: 0,
        }
    }
}

impl Renderer for LocalSlmRenderer {
    fn render(
        &mut self,
        uir: &ValidatedUir,
        facts: &VerifiedFactSet,
    ) -> Result<GeneratedOutput, RenderError> {
        self.invocations += 1;
        let mut child = Command::new(&self.config.python_executable)
            .arg(&self.config.bridge_script)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        let request = LocalSlmRequest {
            model: &self.config.model,
            uir: uir.as_uir(),
            facts,
            temperature: self.config.temperature,
            top_p: self.config.top_p,
            top_k: self.config.top_k,
            max_new_tokens: self.config.max_new_tokens,
            repetition_penalty: self.config.repetition_penalty,
            seed: self.config.seed,
        };
        child
            .stdin
            .take()
            .ok_or_else(|| RenderError::Subprocess("stdin unavailable".into()))?
            .write_all(&serde_json::to_vec(&request)?)?;
        let output = child.wait_with_output()?;
        if !output.status.success() {
            return Err(RenderError::Subprocess(
                String::from_utf8_lossy(&output.stderr).trim().to_owned(),
            ));
        }
        Ok(serde_json::from_slice(&output.stdout)?)
    }

    fn invocation_count(&self) -> u64 {
        self.invocations
    }
}

pub trait VerifiedExecutor {
    fn execute(&self, uir: &ValidatedUir) -> Result<VerifiedFactSet, String>;
}

pub struct FixtureExecutor;
impl VerifiedExecutor for FixtureExecutor {
    fn execute(&self, uir: &ValidatedUir) -> Result<VerifiedFactSet, String> {
        let value = uir.as_uir();
        let metric = value
            .semantics
            .parameters
            .get("metric")
            .cloned()
            .unwrap_or_else(|| "value".into());
        Ok(VerifiedFactSet(vec![VerifiedFact {
            fact_id: format!("{}-{metric}", value.semantics.target.entity_id),
            claim_type: "numeric_fact".into(),
            key: metric,
            value: "100".into(),
            provenance: "fixture:registry-v1".into(),
        }]))
    }
}
