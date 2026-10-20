"""Read-only Git inventory. Ignores are not retroactive access controls."""
import json
import re
import subprocess
from urllib.request import Request, urlopen

from .policy import ROOT, protected_path, utc


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, timeout=120)


def staged_scan():
    paths = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0")
    paths = [p for p in paths if p]
    return {"scope": "INDEX_PATHS_ONLY_NOT_CONTENT_OR_HISTORY", "checked_paths": len(paths),
            "violations": [p for p in paths if protected_path(p)], "timestamp_utc": utc()}


def remote_identity(url):
    # Never serialize credential-bearing origin URLs.
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([\w.-]+)/([\w.-]+?)(?:\.git)?", url.strip())
    if not match:
        raise ValueError("UNSUPPORTED_OR_CREDENTIAL_BEARING_REMOTE")
    return "/".join(match.groups())


def inventory(network_metadata=False):
    head = git("rev-parse", "HEAD").strip()
    repo = remote_identity(git("remote", "get-url", "origin"))
    tracked = [p for p in git("ls-files", "-z").split("\0") if p]
    # Only ancestors of this exact local commit; actual remote SHA is checked below.
    history = git("log", head, "--format=%H", "--", "docs/work_reports").splitlines()
    receipt = {"timestamp_utc": utc(), "repository": repo, "local_head": head,
               "branch": git("branch", "--show-current").strip(),
               "owner_storage_decision": "PRIVATE_REPORTS_LOCAL_ONLY_NO_PRIVATE_REMOTE",
               "current_tracked_report_paths": [p for p in tracked if p.startswith("docs/work_reports/")],
               "current_protected_path_candidates": [p for p in tracked if protected_path(p)],
               "report_history_commits_reachable_from_local_head": history,
               "remote_check": "NOT_EXECUTED", "historical_exposure_remediated": False,
               "credential_content_scan": "NOT_EXECUTED_NO_SECRET_ABSENCE_CLAIM",
               "lfs_objects": "NOT_DOWNLOADED_NOT_AUDITED",
               "private_actions_artifacts": "NOT_AUDITED_AUTHENTICATED_ACCESS_REQUIRED"}
    if network_metadata:
        refs = git("ls-remote", "origin", "HEAD", "refs/heads/main").splitlines()
        receipt["remote_refs"] = dict(line.split()[::-1] for line in refs)
        remote_sha = receipt["remote_refs"].get("refs/heads/main")
        receipt["remote_main_matches_local_head"] = remote_sha == head
        # Small metadata-only requests. No downloads, credentials or mutations.
        api = "https://api.github.com/repos/" + repo
        def get(suffix=""):
            req = Request(api + suffix, headers={"User-Agent": "uir-local-privacy-audit", "Accept": "application/vnd.github+json"})
            with urlopen(req, timeout=30) as response:
                return json.load(response)
        try:
            metadata = get()
            receipt["github_metadata"] = {k: metadata.get(k) for k in
                ("full_name", "private", "visibility", "default_branch", "forks_count", "pushed_at")}
            releases = get("/releases?per_page=100")
            receipt["release_assets"] = [{"release_id": r["id"], "asset_id": a["id"], "name": a["name"], "size": a["size"]}
                                         for r in releases for a in r.get("assets", [])]
            receipt["release_inventory_scope"] = "FIRST_100_RELEASES" if len(releases) == 100 else "ALL_VISIBLE_RELEASES"
            receipt["remote_check"] = "READ_ONLY_VERIFIED"
        except Exception as exc:
            receipt["remote_check"] = "PARTIAL_METADATA_ERROR"
            receipt["remote_error_type"] = type(exc).__name__
    receipt["remote_privacy_gate"] = "BLOCKED_HISTORICAL_EXPOSURE_UNRESOLVED" if history else "NOT_CERTIFIED"
    receipt["staged_scan"] = staged_scan()
    return receipt
