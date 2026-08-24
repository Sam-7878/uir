use crate::{
    DslFrontend, EnglishFrontend, KoreanFrontend, Language, UirCompileError, UniversalIrDraft,
};

#[derive(Default)]
pub struct LanguageRouter {
    ko: KoreanFrontend,
    en: EnglishFrontend,
}

impl LanguageRouter {
    pub fn detect(input: &str) -> Result<Language, UirCompileError> {
        let has_hangul = input
            .chars()
            .any(|ch| ('\u{ac00}'..='\u{d7a3}').contains(&ch));
        let has_latin = input.chars().any(|ch| ch.is_ascii_alphabetic());
        if has_hangul {
            Ok(Language::Ko)
        } else if has_latin {
            Ok(Language::En)
        } else {
            Err(UirCompileError::UnsupportedLanguage)
        }
    }

    pub fn compile(&self, input: &str) -> Result<(Language, UniversalIrDraft), UirCompileError> {
        let language = Self::detect(input)?;
        let draft = match language {
            Language::Ko => self.ko.compile(input)?,
            Language::En => self.en.compile(input)?,
        };
        Ok((language, draft))
    }
}
