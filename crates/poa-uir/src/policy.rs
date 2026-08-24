use std::collections::BTreeSet;

use poa_core::{
    AacoHooks, AbortReason, QuarantineReason, RejectReason, TransitionDescriptor,
    TransitionOutcome, execute_transition,
};
use poa_protocol::EffectivePolicy;
use serde::{Deserialize, Serialize};

use crate::{Enforcement, UirError, ValidatedUir};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PolicyDecision {
    Permit,
    Reject,
    Degrade,
    Quarantine,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyEvaluation {
    pub decision: PolicyDecision,
    pub reason_code: Option<&'static str>,
    pub policy_digest: String,
}

#[derive(Debug, Clone)]
pub struct RuntimeContext {
    pub actor: String,
    pub verified_entities: BTreeSet<String>,
    pub risk_threshold_exceeded: bool,
}

pub fn evaluate_policy(
    uir: &ValidatedUir,
    policy: &EffectivePolicy,
    context: &RuntimeContext,
) -> Result<PolicyEvaluation, UirError> {
    let value = uir.as_uir();
    let digest = poa_protocol::policy_digest(policy)?;
    if context.risk_threshold_exceeded {
        return Ok(result(
            PolicyDecision::Quarantine,
            "UIR_RISK_THRESHOLD",
            digest,
        ));
    }
    let operation = policy
        .operations
        .iter()
        .find(|item| item.name == value.semantics.action);
    let Some(operation) = operation else {
        return Ok(result(PolicyDecision::Reject, "UIR_POLICY_DENIED", digest));
    };
    if !operation
        .allowed_actors
        .iter()
        .any(|actor| actor == &context.actor)
    {
        return Ok(result(PolicyDecision::Reject, "UIR_POLICY_DENIED", digest));
    }
    if !context
        .verified_entities
        .contains(&value.semantics.target.entity_id)
    {
        return Ok(result(
            PolicyDecision::Reject,
            "UIR_ENTITY_UNVERIFIED",
            digest,
        ));
    }
    let enforcement = value
        .policy_constraints
        .iter()
        .map(|item| &item.enforcement)
        .find(|item| {
            matches!(
                item,
                Enforcement::Quarantine
                    | Enforcement::GracefulDegradation
                    | Enforcement::BlockExecution
                    | Enforcement::Reject
            )
        });
    match enforcement {
        Some(Enforcement::Quarantine) => Ok(result(
            PolicyDecision::Quarantine,
            "UIR_POLICY_DENIED",
            digest,
        )),
        Some(Enforcement::GracefulDegradation) => Ok(result(
            PolicyDecision::Degrade,
            "UIR_POLICY_DEGRADED",
            digest,
        )),
        _ => Ok(result(PolicyDecision::Permit, "", digest)),
    }
}

fn result(decision: PolicyDecision, code: &'static str, policy_digest: String) -> PolicyEvaluation {
    PolicyEvaluation {
        decision,
        reason_code: (!code.is_empty()).then_some(code),
        policy_digest,
    }
}

pub fn execute_aaco(uir: &ValidatedUir, evaluation: &PolicyEvaluation) -> TransitionOutcome {
    match evaluation.decision {
        PolicyDecision::Reject => TransitionOutcome::Reject(RejectReason::InvariantViolation(
            evaluation.reason_code.unwrap_or("UIR_POLICY_DENIED").into(),
        )),
        PolicyDecision::Quarantine => {
            TransitionOutcome::Quarantine(QuarantineReason::RiskEvidenceThreshold)
        }
        PolicyDecision::Permit | PolicyDecision::Degrade => {
            let value = uir.as_uir();
            let descriptor = TransitionDescriptor {
                actor: value
                    .semantics
                    .parameters
                    .get("actor")
                    .cloned()
                    .unwrap_or_default(),
                asset: value.semantics.target.entity_id.clone(),
                context: evaluation.policy_digest.clone(),
                operation: value.semantics.action.clone(),
            };
            execute_transition(
                &mut UirHooks {
                    valid: true,
                    state: 0,
                },
                &descriptor,
            )
        }
    }
}

struct UirHooks {
    valid: bool,
    state: u64,
}

impl AacoHooks<String, String, String, String> for UirHooks {
    type Candidate = u64;
    type State = u64;
    fn authorize(
        &self,
        descriptor: &TransitionDescriptor<String, String, String, String>,
    ) -> Result<(), RejectReason> {
        if descriptor.actor.is_empty() {
            Err(RejectReason::DisallowedActor)
        } else {
            Ok(())
        }
    }
    fn validate(
        &self,
        _: &TransitionDescriptor<String, String, String, String>,
    ) -> Result<(), RejectReason> {
        if self.valid {
            Ok(())
        } else {
            Err(RejectReason::InvalidInput("UIR_SEMANTIC_INVALID".into()))
        }
    }
    fn mutate_candidate(
        &mut self,
        _: &TransitionDescriptor<String, String, String, String>,
    ) -> Result<Self::Candidate, AbortReason> {
        Ok(self.state + 1)
    }
    fn reconcile(&mut self, candidate: Self::Candidate) -> Result<(), AbortReason> {
        self.state = candidate;
        Ok(())
    }
    fn state(&self) -> &Self::State {
        &self.state
    }
}
