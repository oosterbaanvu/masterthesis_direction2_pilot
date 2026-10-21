# Pilot 2: qualification of generated data-quality rules

Executed MSc AI feasibility pilot, 21 October 2026. Start with [the measured pilot report](reports/pilot_report.md), [decision](reports/go_no_go.md), and [comparison with Pilot 1](reports/pilot1_vs_pilot2.md).

**Verdict: CONDITIONAL GO for a bounded continuation of Pilot 2 feasibility assessment.** Novelty, independent semantic evaluation and the live same-candidate C/D comparison remain gates before a thesis commitment. Close prior art limits any broad novelty claim. Pilot 1's greater experiment count does not resolve its validity problems or justify preferring it. See [the decision correction](reports/decision_revision.md); the results themselves are unchanged.

Prepared: thirteen-source registry; eleven acquired/scanned sources; all 3,000 released SEC CSVs audited; 24 released model artifacts rescored against the official runner; 360 deterministic scenarios (28,541 actual injected changes); grouped splits; source-shift/formatting sensitivities; safe rule execution and explicit approval lifecycle. Prediction targets are not DQ labels. Optional Kaggle data and live model inference remain blocked, never silently replaced.

```bash
cd /workspace/masterthesis_direction2_pilot
bash scripts/setup.sh
.venv/bin/dqp verify
```

The setup script installs the frozen Python 3.12 environment, verifies/acquires first-party pinned data and runs the tests. Raw data, papers, original predictions, local databases, inference caches and value-level logs are ignored. No paid calls occur during setup or tests.

To rerun all non-LLM experiments without overwriting saved evidence:

```bash
.venv/bin/dqp reproduce --work-dir results/local/reproduction-02
```

Use a new directory each time. Input data are reused; outputs receive a new manifest/freeze. See [reproduction](docs/reproduction.md), [architecture and enforcement](docs/architecture.md), [research protocol](reports/research_design.md), [amendments](reports/protocol_amendments.md), [source qualification](reports/dataset_qualification.md), and [literature](reports/literature_review.md).

A scan with your own **public local CSV** and a JSON list of declarative rules:

```bash
.venv/bin/dqp scan --csv example.csv --rules rules.json --output results/local/findings.json
```

An example rule is `{"id":"positive_amount","kind":"range","columns":["amount"],"parameters":{"min":0},"evidence":"Source contract: payments are nonnegative"}`. This is an illustration, not a validated rule for every financial amount. The research scan executes supplied rules directly; operational deployment uses `dqp service` states and explicit approval. Run `dqp service --help` for its local workflow and read its governance limitations before use.

Experimental model support is disabled by default in `config/models.yaml`. Select a permitted model/endpoint, review prices and input rights, configure positive call/spend caps and secure credentials, and obtain explicit spend authorization before invoking `dqp infer --authorize-paid`. Its provider tests use mocked responses; they are not research measurements. Codex development work is not experimental model inference.
