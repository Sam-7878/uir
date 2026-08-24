use crate::{Intent, Language};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CanonicalOperator {
    And,
    Or,
    Not,
    Except,
    IfThen,
}

pub trait SemanticLexicon {
    fn language(&self) -> Language;
    fn canonical_intent(&self, surface: &str) -> Option<Intent>;
    fn canonical_action(&self, surface: &str) -> Option<&'static str>;
    fn canonical_attribute(&self, surface: &str) -> Option<String>;
    fn canonical_operator(&self, surface: &str) -> Option<CanonicalOperator>;
}

#[derive(Default)]
pub struct KoreanLexicon;
#[derive(Default)]
pub struct EnglishLexicon;

fn attribute(surface: &str) -> Option<String> {
    let value = surface
        .trim_matches(|ch: char| !ch.is_alphanumeric() && ch != '_')
        .to_lowercase();
    let canonical = match value.as_str() {
        "asset" | "assets" | "total_asset" | "total_assets" | "자산" | "총자산" => "assets",
        "revenue" | "revenues" | "sales" | "turnover" | "매출" | "매출액" => "revenue",
        "net_income" | "earnings" | "profit" | "순이익" | "당기순이익" => "net_income",
        "operating_income" | "operating_profit" | "영업이익" => "operating_income",
        _ if value.contains('_')
            && value
                .chars()
                .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit() || ch == '_') =>
        {
            return Some(value);
        }
        _ => return None,
    };
    Some(canonical.into())
}

impl SemanticLexicon for KoreanLexicon {
    fn language(&self) -> Language {
        Language::Ko
    }
    fn canonical_intent(&self, s: &str) -> Option<Intent> {
        if ["비교", "대조"].iter().any(|v| s.contains(v)) {
            Some(Intent::Compare)
        } else if ["원인", "추적"].iter().any(|v| s.contains(v)) {
            Some(Intent::CauseTrace)
        } else if ["요약", "정리"].iter().any(|v| s.contains(v)) {
            Some(Intent::Summarize)
        } else if ["추출", "뽑"].iter().any(|v| s.contains(v)) {
            Some(Intent::Extract)
        } else if ["분석", "검토", "평가", "살펴"]
            .iter()
            .any(|v| s.contains(v))
        {
            Some(Intent::Analyze)
        } else if ["검증", "확인", "조회", "알려", "근거", "출처", "감사"]
            .iter()
            .any(|v| s.contains(v))
        {
            Some(Intent::Verify)
        } else {
            None
        }
    }
    fn canonical_action(&self, s: &str) -> Option<&'static str> {
        self.canonical_intent(s).map(|_| "verify_fact")
    }
    fn canonical_attribute(&self, s: &str) -> Option<String> {
        attribute(s)
    }
    fn canonical_operator(&self, s: &str) -> Option<CanonicalOperator> {
        if s.contains("예외") || s.contains("제외") {
            Some(CanonicalOperator::Except)
        } else if s.contains("그리고") || s.contains("동시에") {
            Some(CanonicalOperator::And)
        } else if s.contains("또는") {
            Some(CanonicalOperator::Or)
        } else if s.contains("아니") || s.contains("않") {
            Some(CanonicalOperator::Not)
        } else if s.contains("만약") || s.contains("이면") {
            Some(CanonicalOperator::IfThen)
        } else {
            None
        }
    }
}

impl SemanticLexicon for EnglishLexicon {
    fn language(&self) -> Language {
        Language::En
    }
    fn canonical_intent(&self, s: &str) -> Option<Intent> {
        if ["compare", "contrast"].iter().any(|v| s.contains(v)) {
            Some(Intent::Compare)
        } else if ["cause", "trace"].iter().any(|v| s.contains(v)) {
            Some(Intent::CauseTrace)
        } else if ["summarize", "summarise", "recap"]
            .iter()
            .any(|v| s.contains(v))
        {
            Some(Intent::Summarize)
        } else if ["extract", "select"].iter().any(|v| s.contains(v)) {
            Some(Intent::Extract)
        } else if [
            "analyze", "analyse", "examine", "review", "assess", "inspect",
        ]
        .iter()
        .any(|v| s.contains(v))
        {
            Some(Intent::Analyze)
        } else if [
            "verify",
            "check",
            "validate",
            "audit",
            "substantiate",
            "cite",
            "what value",
            "report for",
        ]
        .iter()
        .any(|v| s.contains(v))
        {
            Some(Intent::Verify)
        } else {
            None
        }
    }
    fn canonical_action(&self, s: &str) -> Option<&'static str> {
        self.canonical_intent(s).map(|_| "verify_fact")
    }
    fn canonical_attribute(&self, s: &str) -> Option<String> {
        attribute(s)
    }
    fn canonical_operator(&self, s: &str) -> Option<CanonicalOperator> {
        if s.contains("unless") || s.contains("except") {
            Some(CanonicalOperator::Except)
        } else if s.contains(" and ") {
            Some(CanonicalOperator::And)
        } else if s.contains(" or ") {
            Some(CanonicalOperator::Or)
        } else if s.contains(" not ") || s.contains("never") {
            Some(CanonicalOperator::Not)
        } else if s.contains("if ") && s.contains(" then ") {
            Some(CanonicalOperator::IfThen)
        } else {
            None
        }
    }
}
