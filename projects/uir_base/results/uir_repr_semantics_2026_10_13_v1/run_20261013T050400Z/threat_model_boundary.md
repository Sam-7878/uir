# Threat model

Seven fixed untrusted data surfaces and five policy scenarios, with owner-controlled dummy reads. S1 capability set is read-only: attempted writes never gain authority. Payloads are data and are never shell commands. Live snapshot revocation is checked before dispatch; concurrent atomicity remains an assumption. No adaptive model attacks, public network targets, real account data, host compromise or production sandbox are tested. NO_TOOLS is not an attack-success denominator. R-stage60 opportunities remain a separate historical table.
