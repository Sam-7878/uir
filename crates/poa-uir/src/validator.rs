use crate::{ExecutionMode, Intent, UniversalIr};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidationIssue {
    pub code: &'static str,
    pub field: &'static str,
    pub detail: String,
}

#[derive(Debug, Clone)]
pub struct ValidatedUir(UniversalIr);

impl ValidatedUir {
    pub fn as_uir(&self) -> &UniversalIr {
        &self.0
    }
    pub fn into_inner(self) -> UniversalIr {
        self.0
    }
}

pub fn validate(uir: UniversalIr) -> Result<ValidatedUir, Vec<ValidationIssue>> {
    let mut issues = Vec::new();
    if uir.version.trim().is_empty() || uir.metadata.uir_version != uir.version {
        push(
            &mut issues,
            "UIR_SCHEMA_INVALID",
            "version",
            "version mismatch",
        );
    }
    if uir.metadata.request_id.trim().is_empty() {
        push(
            &mut issues,
            "UIR_SCHEMA_INVALID",
            "request_id",
            "empty request id",
        );
    }
    if uir.semantics.target.entity_id.trim().is_empty() {
        push(
            &mut issues,
            "UIR_SCHEMA_INVALID",
            "target",
            "empty entity id",
        );
    }
    if uir.semantics.action.trim().is_empty() {
        push(&mut issues, "UIR_SCHEMA_INVALID", "action", "empty action");
    }
    if uir
        .semantics
        .conditions
        .iter()
        .any(|condition| !condition.is_well_formed())
        || uir
            .policy_constraints
            .iter()
            .any(|constraint| !constraint.condition.is_well_formed())
    {
        push(
            &mut issues,
            "UIR_SCHEMA_INVALID",
            "conditions",
            "malformed condition tree",
        );
    }
    if uir.execution_contract.allowed_operations.is_empty()
        || !uir
            .execution_contract
            .allowed_operations
            .contains(&uir.semantics.action)
    {
        push(
            &mut issues,
            "UIR_SEMANTIC_INVALID",
            "allowed_operations",
            "requested action is not allowed by the execution contract",
        );
    }
    if matches!(uir.semantics.intent, Intent::Compare)
        && !uir.semantics.parameters.contains_key("period")
    {
        push(
            &mut issues,
            "UIR_SEMANTIC_INVALID",
            "parameters",
            "COMPARE requires operands",
        );
    }
    if matches!(
        uir.execution_contract.execution_mode,
        ExecutionMode::VerifiedOnly
    ) && !uir.output_contract.provenance_required
    {
        push(
            &mut issues,
            "UIR_SEMANTIC_INVALID",
            "output_contract",
            "VERIFIED_ONLY requires provenance",
        );
    }
    if uir.output_contract.numeric_exactness
        && !uir
            .output_contract
            .allowed_claim_types
            .iter()
            .any(|value| value == "numeric_fact")
    {
        push(
            &mut issues,
            "UIR_SEMANTIC_INVALID",
            "numeric_exactness",
            "numeric exactness requires numeric facts",
        );
    }
    if uir.output_contract.allowed_claim_types.is_empty() {
        push(
            &mut issues,
            "UIR_SCHEMA_INVALID",
            "allowed_claim_types",
            "at least one claim type is required",
        );
    }
    if issues.is_empty() {
        Ok(ValidatedUir(uir))
    } else {
        Err(issues)
    }
}

fn push(issues: &mut Vec<ValidationIssue>, code: &'static str, field: &'static str, detail: &str) {
    issues.push(ValidationIssue {
        code,
        field,
        detail: detail.into(),
    });
}
