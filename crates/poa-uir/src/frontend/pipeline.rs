use regex::Regex;

use super::{lexicon::SemanticLexicon, normalization::normalize};
use crate::{Language, UirCompileError, UniversalIrDraft};

pub fn compile_typed(
    input: &str,
    language: Language,
    lexicon: &dyn SemanticLexicon,
) -> Result<UniversalIrDraft, UirCompileError> {
    super::reject_adversarial(input)?;
    let normalized = normalize(input, language);
    debug_assert_eq!(normalized.language, lexicon.language());
    let intent = lexicon
        .canonical_intent(&normalized.folded)
        .ok_or_else(|| UirCompileError::Incomplete("intent".into()))?;
    let action = lexicon
        .canonical_action(&normalized.folded)
        .ok_or_else(|| UirCompileError::Incomplete("action".into()))?;
    let entity = extract_entity(&normalized.original)
        .ok_or_else(|| UirCompileError::Incomplete("target".into()))?;
    let metric = extract_attribute(&normalized.folded, lexicon)
        .ok_or_else(|| UirCompileError::Incomplete("metric".into()))?;
    let period = capture(&normalized.original, r"(20\d{2})")
        .ok_or_else(|| UirCompileError::Incomplete("period".into()))?;
    let mut draft = super::ko::build(intent, entity, metric, period, &normalized.original)?;
    draft.semantics.action = action.into();
    Ok(draft)
}

fn extract_entity(input: &str) -> Option<String> {
    // ASCII boundaries are intentional: a ticker may be directly followed by a
    // Korean particle, which Unicode `\b` does not consider a boundary.
    let candidates =
        Regex::new(r"(?:^|[^A-Za-z0-9.-])([A-Z][A-Z0-9.-]{0,15})(?:$|[^A-Za-z0-9.-])").ok()?;
    const RESERVED: &[&str] = &[
        "A", "AND", "OR", "NOT", "IF", "THEN", "USD", "JSON", "UIR", "SLM",
    ];
    let result = candidates
        .captures_iter(input)
        .filter_map(|capture| capture.get(1).map(|v| v.as_str()))
        .find(|value| !RESERVED.contains(value))
        .map(str::to_owned);
    result
}

fn extract_attribute(input: &str, lexicon: &dyn SemanticLexicon) -> Option<String> {
    let cleaned = input.replace(['?', ',', ';', ':', '.', '(', ')', '\'', '\"'], " ");
    cleaned
        .split_whitespace()
        .find_map(|token| lexicon.canonical_attribute(token))
}

fn capture(input: &str, pattern: &str) -> Option<String> {
    Regex::new(pattern)
        .ok()?
        .captures(input)?
        .get(1)
        .map(|value| value.as_str().to_owned())
}
