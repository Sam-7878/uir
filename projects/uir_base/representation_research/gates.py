"""Executable evidence boundaries; metadata alone is never blanket scientific approval."""
from .baseline import authoritative_report


def check_claim(record):
    if record.get("endpoint") == "QUERY_AWARE_SELECTION" and not record.get("raw_request_present"):
        raise ValueError("ENUMERATION_IS_NOT_QUERY_AWARE")
    if record.get("whole_output_AUCR_measured") and not record.get("all_displayed_output_scored"):
        raise ValueError("STRUCTURED_ONLY_IS_NOT_WHOLE_OUTPUT")
    if record.get("source_scope") == "entire_parent_annual_report" and not record.get("parent_report_bytes_verified"):
        raise ValueError("PAGE_IS_NOT_PARENT_REPORT")
    if record.get("human_validated") and not record.get("actual_human_label_count", 0):
        raise ValueError("AI_ONLY_IS_NOT_HUMAN_VALIDATED")
    if record.get("confirmatory") and (not record.get("verified_family_disjoint") or set(record.get("dev_families", [])) & set(record.get("holdout_families", []))):
        raise ValueError("HOLDOUT_FAMILY_NOT_DISJOINT")
    if record.get("capability_parity") and record.get("UIR_source_hash") != record.get("specialized_source_hash"):
        raise ValueError("DIFFERENTIAL_BASELINE_FACT_PRIVILEGE")
    if record.get("UIR_accuracy_superiority") and record.get("UIR_accuracy", 0) <= record.get("specialized_accuracy", 0):
        raise ValueError("EQUAL_IS_NOT_SUPERIOR")
    if record.get("submission_ready") and not all(record.get(k) is True for k in ("author_approval", "institution_approval", "rights_approved", "live_journal_rules_verified")):
        return "BLOCKED"
    return "PASS_SCOPED"
