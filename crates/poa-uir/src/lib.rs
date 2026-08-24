pub mod canonical;
pub mod compiler;
pub mod condition;
pub mod equivalence;
pub mod error;
pub mod evidence;
pub mod frontend;
pub mod model;
pub mod output_contract;
pub mod policy;
pub mod resolution;
pub mod validator;

pub use canonical::{canonicalize_uir, semantic_digest, uir_digest};
pub use compiler::{CompileOptions, compile_input};
pub use condition::{Condition, ScalarValue};
pub use equivalence::{ComparisonMode, equivalent};
pub use error::{UirCompileError, UirError};
pub use evidence::*;
pub use frontend::{DslFrontend, EnglishFrontend, KoreanFrontend, LanguageRouter};
pub use model::*;
pub use output_contract::*;
pub use policy::*;
pub use resolution::*;
pub use validator::{ValidatedUir, ValidationIssue, validate};

#[cfg(test)]
mod tests;
