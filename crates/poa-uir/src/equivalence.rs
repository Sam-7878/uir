use crate::{UirError, UniversalIr, canonicalize_uir, semantic_digest};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ComparisonMode {
    ExactStructural,
    SemanticCanonical,
}

pub fn equivalent(
    left: &UniversalIr,
    right: &UniversalIr,
    mode: ComparisonMode,
) -> Result<bool, UirError> {
    match mode {
        ComparisonMode::ExactStructural => Ok(canonicalize_uir(left)? == canonicalize_uir(right)?),
        ComparisonMode::SemanticCanonical => Ok(semantic_digest(left)? == semantic_digest(right)?),
    }
}
