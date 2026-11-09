# V4.4 HETE: Track B live inference

The custom runner generates proposals through local Ollama and applies the same
record authority, scoped grant, proof/current-state/nonce check and SQLite
executor to a flat dictionary and a nominal typed carrier. Offline gold scoring
does not enter the runtime. No real payment, mail, calendar or cloud services
are invoked. AgentDojo is separately registered: native tasks, attack generation,
mock environment and oracles with a custom JSON frontend, not a leaderboard.

Use Ubuntu 26.04.1 and the workspace .venv_cuda Python. Review the local
registration and file hashes before running. Registered experiments write only
to the V4.4 result namespace. The inference runner is resumable by saved request
intent, not by resampling failed requests. Do not run it on an existing delivery
to reproduce published numbers; use the raw-evidence offline path.

Clean extraction (no GPU/server needed):
1. Extract the private reproduction ZIP into a new directory. From its root run
   `python -B -m pytest tests/uir_security/test_scie_v4_4.py -q -p no:cacheprovider`.
2. Run `python -B -m projects.uir_security.evaluation.scie_v4_4.aggregate`.
3. Run `python -B -m projects.uir_security.evaluation.scie_v4_4.validate_evidence --extracted`.
   This checks saved custom model transport and replays actual SQLite/outbox
   effects; old V4.3 and native package origins are not reproduced by extraction.
4. Journal and generic preprint source ZIPs compile separately using the included
   README_BUILD. Raw evidence is not inside either manuscript package.

This bundle is local-only; no coauthor or institutional approval is implied.
