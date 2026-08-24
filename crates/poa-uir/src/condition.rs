use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ScalarValue {
    String(String),
    Integer(i64),
    Boolean(bool),
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
    Gt {
        lhs: String,
        rhs: ScalarValue,
    },
    Lt {
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
            Self::Eq { lhs, .. } | Self::Gt { lhs, .. } | Self::Lt { lhs, .. } => {
                !lhs.trim().is_empty()
            }
            Self::Not { expr } => expr.is_well_formed(),
            Self::And { exprs } | Self::Or { exprs } => {
                exprs.len() >= 2 && exprs.iter().all(Self::is_well_formed)
            }
            Self::Except { rule, exception } => rule.is_well_formed() && exception.is_well_formed(),
        }
    }
}
