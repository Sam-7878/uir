use serde::{Deserialize, Serialize};

use crate::{CompileOptions, UirCompileError, UniversalIr, compile_input};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SemanticResolutionStatus {
    Resolved,
    NeedsClarification,
    Unsupported,
    Invalid,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticResolution {
    pub status: SemanticResolutionStatus,
    pub missing_slots: Vec<String>,
    pub reason: Option<String>,
    pub uir: Option<UniversalIr>,
}

pub fn resolve_input(input: &str, options: &CompileOptions) -> SemanticResolution {
    match compile_input(input, options) {
        Ok(uir) => SemanticResolution {
            status: SemanticResolutionStatus::Resolved,
            missing_slots: vec![],
            reason: None,
            uir: Some(uir),
        },
        Err(UirCompileError::Incomplete(slot)) => SemanticResolution {
            status: SemanticResolutionStatus::NeedsClarification,
            missing_slots: vec![slot],
            reason: Some("MISSING_REQUIRED_SLOT".into()),
            uir: None,
        },
        Err(UirCompileError::UnsupportedLanguage) => SemanticResolution {
            status: SemanticResolutionStatus::Unsupported,
            missing_slots: vec![],
            reason: Some("UNSUPPORTED_LANGUAGE".into()),
            uir: None,
        },
        Err(UirCompileError::Malformed(reason)) => SemanticResolution {
            status: SemanticResolutionStatus::Invalid,
            missing_slots: vec![],
            reason: Some(reason),
            uir: None,
        },
    }
}
