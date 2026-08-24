use crate::Language;

#[derive(Debug, Clone)]
pub struct NormalizedInput {
    pub original: String,
    pub folded: String,
    pub language: Language,
}

pub fn normalize(input: &str, language: Language) -> NormalizedInput {
    let whitespace = input.split_whitespace().collect::<Vec<_>>().join(" ");
    let punctuation = whitespace
        .replace(['\u{2018}', '\u{2019}'], "'")
        .replace(['\u{201c}', '\u{201d}'], "\"")
        .replace(['\u{2013}', '\u{2014}'], "-");
    NormalizedInput {
        original: punctuation.clone(),
        folded: punctuation.to_lowercase(),
        language,
    }
}
