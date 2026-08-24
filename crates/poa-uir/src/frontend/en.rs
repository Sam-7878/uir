use super::lexicon::EnglishLexicon;
use crate::{DslFrontend, Language, UirCompileError, UniversalIrDraft};

#[derive(Default)]
pub struct EnglishFrontend;

impl DslFrontend for EnglishFrontend {
    fn language(&self) -> Language {
        Language::En
    }

    fn compile(&self, input: &str) -> Result<UniversalIrDraft, UirCompileError> {
        super::pipeline::compile_typed(input, Language::En, &EnglishLexicon)
    }
}
