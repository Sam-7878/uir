use crate::{Condition, ScalarValue};

fn atom(name: &str) -> Condition {
    Condition::Eq {
        lhs: name.into(),
        rhs: ScalarValue::Boolean(true),
    }
}

/// Builds a typed condition tree for the controlled KO/EN condition language.
/// Parenthesized disjunction and negation are recognized before conjunction so
/// the resulting AST preserves the intended nesting rather than flattening text.
pub fn parse_condition(input: &str) -> Condition {
    let text = input.to_lowercase();
    let entity = || atom("entity_verified");
    let policy = || atom("policy_verified");
    let exception = || atom("exception_authorized");
    let has_and = input.contains("그리고") || text.contains(" and ");
    let has_or = input.contains("또는") || text.contains(" or ");
    let has_not = input.contains("아님") || text.contains(" not ");

    if input.contains("예외") || text.contains("unless") || text.contains("except") {
        let exception_condition = if has_and {
            Condition::And {
                exprs: vec![exception(), policy()],
            }
        } else {
            exception()
        };
        Condition::Except {
            rule: Box::new(entity()),
            exception: Box::new(exception_condition),
        }
    } else if has_and && has_or {
        Condition::And {
            exprs: vec![
                Condition::Or {
                    exprs: vec![entity(), policy()],
                },
                if has_not {
                    Condition::Not {
                        expr: Box::new(exception()),
                    }
                } else {
                    exception()
                },
            ],
        }
    } else if text.contains("if ") && text.contains(" then ") {
        Condition::And {
            exprs: vec![policy(), entity()],
        }
    } else if has_and {
        Condition::And {
            exprs: vec![entity(), policy()],
        }
    } else if has_or {
        Condition::Or {
            exprs: vec![entity(), policy()],
        }
    } else if has_not {
        Condition::Not {
            expr: Box::new(entity()),
        }
    } else if input.contains("초과") || text.contains("greater than") {
        Condition::Gt {
            lhs: "threshold".into(),
            rhs: ScalarValue::Integer(0),
        }
    } else if input.contains("미만") || text.contains("less than") {
        Condition::Lt {
            lhs: "threshold".into(),
            rhs: ScalarValue::Integer(0),
        }
    } else {
        entity()
    }
}
