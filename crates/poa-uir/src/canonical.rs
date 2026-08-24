use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

use crate::{UirError, UniversalIr};

pub fn canonicalize_uir(uir: &UniversalIr) -> Result<Vec<u8>, UirError> {
    Ok(poa_protocol::canonicalize_value(uir)?)
}

pub fn uir_digest(uir: &UniversalIr) -> Result<String, UirError> {
    Ok(digest(canonicalize_uir(uir)?))
}

pub fn semantic_digest(uir: &UniversalIr) -> Result<String, UirError> {
    #[derive(Serialize)]
    struct SemanticView<'a> {
        version: &'a str,
        domain: &'a str,
        semantics: &'a crate::Semantics,
        policy_constraints: &'a [crate::PolicyConstraint],
        execution_contract: &'a crate::ExecutionContract,
        output_contract: &'a crate::OutputContract,
    }
    let view = SemanticView {
        version: &uir.version,
        domain: &uir.metadata.domain,
        semantics: &uir.semantics,
        policy_constraints: &uir.policy_constraints,
        execution_contract: &uir.execution_contract,
        output_contract: &uir.output_contract,
    };
    Ok(digest(poa_protocol::canonicalize_value(&view)?))
}

pub fn canonical_value<T: Serialize>(value: &T) -> Result<Value, UirError> {
    Ok(serde_json::from_slice(&poa_protocol::canonicalize_value(
        value,
    )?)?)
}

fn digest(bytes: Vec<u8>) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
}
