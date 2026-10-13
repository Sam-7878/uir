# Offline reproduction

The executed cleanroom.py creates a NEW --copies venv in /tmp, installs only
hash-pinned wheels with --no-index --no-deps --require-hashes, sanitizes the
environment and runs the frozen verifier under Python -I. It recreates 31
historical scientific files and all 800 FinQA raw-to-summary scores without a
development source import. Missing rfc8785 is an executed negative failure.

requirements.lock and wheel_manifest.json pin Linux x86_64 CPython 3.14 wheels.
environment.lock pins Python and the exact observed Rust/Cargo build IDs plus
Cargo.lock. No torch/CUDA/model dependency is required for CPU score replay.
Official FinQA parity additionally needs the separately packaged tqdm/sympy/mpmath
wheels and lock; these are not needed for the original 31/800 replay.

The Rust dependency source vendor is generated from Cargo.lock. Cargo's own
checksums govern vendor content. A fresh toolchain still needs provisioning with
the exact compiler build ID; a wheel/vendor archive does not contain a Rust or
Python interpreter. Offline vendor initially failed on missing platform crates;
locked dependency fetching completed the cache before packaging.

This is a fresh virtual environment on the same physical host, not an independently
appointed human operator or third machine. Environment sanitation and extracted
module-path checks are not OS/native-code isolation or proof that no hidden host
file could ever be opened. Replay did not call models; network disable was not
enforced by an OS firewall. Do not elevate these scoped facts into security proofs.
