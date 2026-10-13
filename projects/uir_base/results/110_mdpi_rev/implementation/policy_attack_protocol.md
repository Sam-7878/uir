# Policy opportunity / action protocol

`next_policy.py` executes ten finite in-memory action fixtures for each of
enforced-contract, unguarded-tool, refuse-only-tool and no-tool controls. These
have identical finite read/write opportunities except the intentionally no-tool
condition. Six requests are prohibited, four allowed. Actual effects are recorded;
no host read, write, secret exfiltration, or real account operation is attempted.

Enforced contract: 0/6 prohibited effects and 0/4 false denials. Unguarded control:
6/6 prohibited effects. Refuse-only: 0/6 prohibited effects but 4/4 false denials.
No-tool action rates are NOT_APPLICABLE with zero execution opportunities, not
evidence of successful attack blocking.

Explicit authority checks cover entity, period and unit mismatch at the new
wrapper boundary; do not attribute unit checks to shared bind_references, whose
matching does not include unit. Approval revocation and snapshot mismatch are
revalidated before effect. User, document, tool-output and code-mixed injection
positions are synthetic data/control-boundary checks, not an adversarial-model
success-rate benchmark. Trusted policy/registry/executor and non-compromised host
are assumptions. Broader deployed agents and registry compromise are NOT_TESTED.

Legacy 500 mutation inputs were reconstructed from the pinned seeded generator;
1,500 gate classifications reproduce the old 30 aggregate rows. Original
mutated-input captures were not recorded. The map says RECONSTRUCTED, not raw.
The legacy safe_handling classifier does not assess generated output and is not
evidence that numeric registry tampering is safe. No fresh model costs are incurred
by this reconstruction; no inference-based robustness claim follows.
