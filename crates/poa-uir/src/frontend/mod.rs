mod en;
mod ko;
pub mod lexicon;
mod normalization;
mod pipeline;
mod router;

pub use en::EnglishFrontend;
pub use ko::KoreanFrontend;
pub use lexicon::{CanonicalOperator, EnglishLexicon, KoreanLexicon, SemanticLexicon};
pub use router::LanguageRouter;

use crate::{Language, UirCompileError, UniversalIrDraft};

pub trait DslFrontend {
    fn language(&self) -> Language;
    fn compile(&self, input: &str) -> Result<UniversalIrDraft, UirCompileError>;
}

pub(crate) fn reject_adversarial(input: &str) -> Result<(), UirCompileError> {
    let lowered = input.to_lowercase();
    // Compatibility concepts retained from /hete/hete_dsl: security checks
    // precede semantic parsing, entity identifiers remain lexer-owned, and
    // network/fiction requests fail closed. No SLM-produced slot may replace
    // the captured target.
    let markers = [
        "ignore previous",
        "system:",
        "developer:",
        "<|",
        "지시를 무시",
        "시스템 메시지",
        "역할을 바꿔",
        "인터넷에서 검색",
        "외부에서 검색",
        "가상의 판결문",
        "허구로 작성",
        "jailbreak",
    ];
    if markers.iter().any(|marker| lowered.contains(marker))
        || input.chars().any(|ch| {
            matches!(
                ch,
                '\u{202e}' | '\u{2066}' | '\u{2067}' | '\u{2068}' | '\u{2069}'
            )
        })
    {
        return Err(UirCompileError::Malformed("injection marker".into()));
    }
    Ok(())
}
mod condition_parser;
