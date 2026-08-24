use thiserror::Error;

#[derive(Debug, Error)]
pub enum UirError {
    #[error("serialization failed: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("validation failed: {0}")]
    Validation(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum UirCompileError {
    #[error("unsupported language")]
    UnsupportedLanguage,
    #[error("ambiguous or incomplete command: {0}")]
    Incomplete(String),
    #[error("malformed or adversarial command: {0}")]
    Malformed(String),
}
