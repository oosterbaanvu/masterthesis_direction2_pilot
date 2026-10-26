# Working free-model configuration

The successful provider is **local CPU llama.cpp**, model `Qwen/Qwen2.5-Coder-7B-Instruct`, official GGUF revision `13fb94bfda8c8cf22497dc57b78f391a9acb426a`, quantization `Q4_K_M`, Apache 2.0. Weight SHA-256: `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`. Exact source commit: `620d2225cc436ab0b001e3200e590e3b286ef9ab`. The original built server binary SHA-256 is `4c7c45ebcace8895dbea0d2301c615141e1e3d7858c3f1115915acda5ddf6286`. The archive build inherited an outer-repository Git label; explicit source commit/archive checksum, not that embedded label, establishes source provenance.

Gemini key and explicit free-project confirmation were absent. No Gemini generation/model substitution was attempted. A key alone would not prove an unbilled account; this route remains optional. No paid API, rented GPU or automatic billing fallback exists in the local runner. Existing historical paid-model proposals are superseded for this execution.

Ollama 0.40.11 was acquired from its official release and checksum verified (`results/execution/acquisition.json`). The user-local installation succeeded; `serve` failed attempting `/home/agent/.ollama/id_ed25519` because the home directory is read-only. No HOME override or root workaround was used. Registry access was also restricted. The permitted equivalent runtime actually loaded verified weights and generated the saved responses; changing runtime is not claimed to have fixed the Ollama registry path.

## Measured resources and performance

Cgroup limits are four equivalent vCPUs and 32 GiB RAM, with no NVIDIA device. The server binds only to literal 127.0.0.1, has one inference slot and requires a random local bearer token in an ignored mode-600 file. Model requests use an 8,192-token context, 2,048 output-token ceiling, four CPU threads, zero GPU layers, temperature 0, top-p 1, repeat penalty 1, seeds 11/23/37 and JSON-constrained output. No public preview or hosted Ollama route is used.

Across 56 real calls: median wall time **111.7 s**, median measured prompt throughput **30.38 tokens/s**, median generation throughput **4.14 tokens/s**; peak observed server RSS **9.01 GiB**. 4 early request records have an instrumentation sentinel of zero, meaning unavailable, not zero RAM. The monitor was corrected without rewriting those records. Some requests queued behind a second client while the server remained single-slot; walltime includes queueing. Native token speeds exclude that queue. Weight acquisition took 346.9 seconds; build/acquisition time is separate from inference.

Actual reported token usage is **102796 input + 21854 output = 124650 total**. Server usage and prefix-cache details are preserved per call; do not interpret cached prefix tokens as new processing speed. API inference charge is **US$0**. Infrastructure, electricity and labour were not priced and are not claimed free.

## Paper model and alternatives

The inspected LeDQeR uses GLM-4.7-Flash AWQ4, Qwen3-Coder-30B-A3B AWQ4 and Gemma-4-31B FP8, not this 7B Q4 GGUF configuration. Akella reports Gemma-3-12B/Qwen2.5-Coder-32B. Model size, family, quantization, prompt context and hardware all differ; no paper performance equivalence follows.

`large_model_feasibility.json` records Qwen3-Coder-30B-A3B's 18,556,689,568-byte community GGUF and prior sizing. The full expert weights remain resident despite 3B active parameters. Short-context memory sizing is plausible, but the current disk footprint fails the eight-GiB headroom policy without deliberate cache cleanup. Exact AWQ/GPU execution is unavailable. No 30B weights were fully downloaded, loaded or benchmarked; neither speed nor inherent CPU impossibility is inferred. The viable 7B run was retained. The 3B fallback was unnecessary and was not silently mixed into conditions.

## Reuse and restart

Run `PYTHONPATH=src envs/final/.venv/bin/python scripts/execution/acquire_local.py` to verify/reuse or acquire/build pinned artifacts, then `... scripts/execution/start_local.py`. The latter verifies authenticated model listing and tokenization without adding a generation request. Cached outputs can be evaluated with the server stopped. Full commands and dataset restoration are in [reproduction](reproduction.md). The durable cache quarantines incomplete requests; successful matching calls are reused. Runtime/hardware changes can alter new generation despite fixed seed; cached output rescoring is the reproducibility guarantee.
