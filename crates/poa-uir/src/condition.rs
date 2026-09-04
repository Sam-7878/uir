use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ScalarType {
    String,
    Integer,
    Boolean,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ScalarValue {
    String(String),
    Integer(i64),
    Boolean(bool),
}

impl ScalarValue {
    pub fn scalar_type(&self) -> ScalarType {
        match self {
            Self::String(_) => ScalarType::String,
            Self::Integer(_) => ScalarType::Integer,
            Self::Boolean(_) => ScalarType::Boolean,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(
    tag = "operator",
    rename_all = "SCREAMING_SNAKE_CASE",
    deny_unknown_fields
)]
pub enum Condition {
    Eq {
        lhs: String,
        rhs: ScalarValue,
    },
    Ne {
        lhs: String,
        rhs: ScalarValue,
    },
    Gt {
        lhs: String,
        rhs: ScalarValue,
    },
    Ge {
        lhs: String,
        rhs: ScalarValue,
    },
    Lt {
        lhs: String,
        rhs: ScalarValue,
    },
    Le {
        lhs: String,
        rhs: ScalarValue,
    },
    Not {
        expr: Box<Condition>,
    },
    And {
        exprs: Vec<Condition>,
    },
    Or {
        exprs: Vec<Condition>,
    },
    Except {
        rule: Box<Condition>,
        exception: Box<Condition>,
    },
}

impl Condition {
    pub fn is_well_formed(&self) -> bool {
        match self {
            Self::Eq { lhs, .. }
            | Self::Ne { lhs, .. }
            | Self::Gt { lhs, .. }
            | Self::Ge { lhs, .. }
            | Self::Lt { lhs, .. }
            | Self::Le { lhs, .. } => !lhs.trim().is_empty(),
            Self::Not { expr } => expr.is_well_formed(),
            Self::And { exprs } | Self::Or { exprs } => {
                exprs.len() >= 2 && exprs.iter().all(Self::is_well_formed)
            }
            Self::Except { rule, exception } => {
                rule.is_well_formed() && exception.is_well_formed()
            }
        }
    }

    pub fn type_check(&self, env: &HashMap<String, ScalarType>) -> Result<(), String> {
        match self {
            Self::Eq { lhs, rhs } | Self::Ne { lhs, rhs } => {
                if let Some(expected_type) = env.get(lhs) {
                    if *expected_type != rhs.scalar_type() {
                        return Err(format!(
                            "Type mismatch on {}: expected {:?}, got {:?}",
                            lhs,
                            expected_type,
                            rhs.scalar_type()
                        ));
                    }
                }
                Ok(())
            }
            Self::Gt { lhs, rhs }
            | Self::Ge { lhs, rhs }
            | Self::Lt { lhs, rhs }
            | Self::Le { lhs, rhs } => {
                if rhs.scalar_type() != ScalarType::Integer {
                    return Err(format!(
                        "Relational operator requires integer rhs, got {:?}",
                        rhs.scalar_type()
                    ));
                }
                if let Some(expected_type) = env.get(lhs) {
                    if *expected_type != ScalarType::Integer {
                        return Err(format!(
                            "Relational operator on {} requires integer type, got {:?}",
                            lhs, expected_type
                        ));
                    }
                }
                Ok(())
            }
            Self::Not { expr } => expr.type_check(env),
            Self::And { exprs } | Self::Or { exprs } => {
                for e in exprs {
                    e.type_check(env)?;
                }
                Ok(())
            }
            Self::Except { rule, exception } => {
                rule.type_check(env)?;
                exception.type_check(env)?;
                Ok(())
            }
        }
    }

    pub fn eval(&self, env: &HashMap<String, ScalarValue>) -> Result<bool, String> {
        match self {
            Self::Eq { lhs, rhs } => match env.get(lhs) {
                Some(val) => Ok(val == rhs),
                None => Ok(false),
            },
            Self::Ne { lhs, rhs } => match env.get(lhs) {
                Some(val) => Ok(val != rhs),
                None => Ok(true),
            },
            Self::Gt { lhs, rhs } => match env.get(lhs) {
                Some(val) => Ok(val > rhs),
                None => Ok(false),
            },
            Self::Ge { lhs, rhs } => match env.get(lhs) {
                Some(val) => Ok(val >= rhs),
                None => Ok(false),
            },
            Self::Lt { lhs, rhs } => match env.get(lhs) {
                Some(val) => Ok(val < rhs),
                None => Ok(false),
            },
            Self::Le { lhs, rhs } => match env.get(lhs) {
                Some(val) => Ok(val <= rhs),
                None => Ok(false),
            },
            Self::Not { expr } => expr.eval(env).map(|r| !r),
            Self::And { exprs } => {
                for e in exprs {
                    if !e.eval(env)? {
                        return Ok(false);
                    }
                }
                Ok(true)
            }
            Self::Or { exprs } => {
                for e in exprs {
                    if e.eval(env)? {
                        return Ok(true);
                    }
                }
                Ok(false)
            }
            Self::Except { rule, exception } => {
                let r = rule.eval(env)?;
                let ex = exception.eval(env)?;
                Ok(r && !ex)
            }
        }
    }
}
