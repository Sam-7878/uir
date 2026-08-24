use sha2::{Digest, Sha256};

use crate::{LanguageRouter, Metadata, UirCompileError, UniversalIr};

#[derive(Debug, Clone)]
pub struct CompileOptions {
    pub request_id: String,
    pub created_at: String,
    pub compiler_version: String,
}

impl Default for CompileOptions {
    fn default() -> Self {
        Self {
            request_id: "request-unknown".into(),
            created_at: "1970-01-01T00:00:00Z".into(),
            compiler_version: env!("CARGO_PKG_VERSION").into(),
        }
    }
}

pub fn compile_input(
    input: &str,
    options: &CompileOptions,
) -> Result<UniversalIr, UirCompileError> {
    let (language, draft) = LanguageRouter::default().compile(input)?;
    let source_hash = format!("sha256:{}", hex::encode(Sha256::digest(input.as_bytes())));
    Ok(UniversalIr {
        version: "1.0".into(),
        metadata: Metadata {
            uir_version: "1.0".into(),
            request_id: options.request_id.clone(),
            source_language: language,
            source_hash,
            compiler_version: options.compiler_version.clone(),
            domain: draft.domain,
            created_at: options.created_at.clone(),
        },
        semantics: draft.semantics,
        policy_constraints: draft.policy_constraints,
        execution_contract: draft.execution_contract,
        output_contract: draft.output_contract,
    })
}
