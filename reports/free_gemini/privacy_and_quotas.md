# Privacy, licensing, model eligibility and quota evidence

Primary Google pages were fetched on 21 October 2026 and hashed in `results/free_gemini/public_sources.json`. Original pages remain in ignored cache. This is an own-account batch research experiment, not a hosted API application offered to third-party end users.

## Model and free-tier availability

The official [Gemini 2.5 Flash model page](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash) states that access to 2.5 models is limited to users who actively used them in the past. It lists stable model code `gemini-2.5-flash`, JSON output, thinking support and text output. The [deprecations page](https://ai.google.dev/gemini-api/docs/deprecations) currently announces no shutdown date for this stable model. These observations do **not** prove a newly configured project is eligible.

The [pricing page](https://ai.google.dev/gemini-api/docs/pricing) lists free input and output for this model on the free tier. A project with active billing uses paid-service conditions and can incur charges; no client-side zero-dollar budget can turn that project into a free project. Therefore the implementation requires an explicitly confirmed non-billed project and never enables billing, tools, search grounding, paid caching, batch/flex/priority service or another provider.

The [rate-limit page](https://ai.google.dev/gemini-api/docs/rate-limits) directs users to their active limits in AI Studio. Limits apply **per project**, across keys, and distinguish RPM, input TPM and RPD; daily limits reset at midnight Pacific time. The actual quota is currently **UNKNOWN**. Local caps of 20/day and roughly 2/minute are conservative execution choices, not a guaranteed allocation. HTTP 429 is preserved and stops the batch; another key/project is not used to evade it.

## Data processing terms

The current [additional terms](https://ai.google.dev/gemini-api/terms) state that unpaid-service inputs/outputs can be used for product improvement and human review, and instruct users not to submit sensitive, confidential or personal information. They also contain an **EEA/Switzerland/UK exception**: the paid-services subsection on how Google uses data applies there even to unpaid API quota. Paid-services processing says prompts/responses are not used for product improvement, while limited abuse-monitoring retention remains. Location and account applicability must not be inferred solely from the cloud host's timezone.

These regional terms are more nuanced than the pricing table's generic “used to improve products: Yes.” The pilot therefore uses the stricter common denominator: **public non-personal source descriptions and entirely synthetic examples only**, without relying on the regional exception to justify sending customer records. A separate restriction on making API clients available to EEA/Swiss/UK end users must be checked before deploying a public/end-user service; this research run does not deploy one.

## Qualified input scope

| Source | Transmitted input | Basis and restriction |
|---|---|---|
| UCI Credit, Yeh (2009), DOI 10.24432/C55S3H | Feature schema, public source descriptions and explicitly marked inherited/provisional controls | UCI CC BY 4.0 metadata, attribution/DOI retained. **No customer rows, IDs, demographic observations or default targets** |
| UCI Bank Marketing, Moro et al. (2014), DOI 10.24432/C5K306 | Schema, publicly documented categories/sentinels and marked controls | UCI CC BY 4.0 metadata. **No individual records or `y` labels**; unknown/sentinel conventions remain explicit |
| UCI White Wine, Cortez et al. (2009), DOI 10.24432/C56S3T | Measurement schema and source descriptions | UCI CC BY 4.0 metadata. No original rows or sensory `quality` target in the prompts |
| Synthetic balanced journals | Self-authored schema/contract and five conspicuously synthetic rows | No real company, bank, customer or financial filing. Semantic assumptions are stipulated for a software scenario, not human-adjudicated financial gold |

CC BY 4.0 information: https://creativecommons.org/licenses/by/4.0/. Contexts retain their source citations, licence basis and contract hashes. The two documentation conditions vary **additional** documentation; installed controls remain visible in both. Hence the withheld condition is not a completely information-free/source-agnostic setting.

All three UCI identities/DOIs were checked through its metadata API, and all three authoritative landing pages were fetched and contained the CC BY 4.0 licence link. Exact page hashes and licence evidence are in `results/free_gemini/uci_licence_verification.json`; the API metadata alone does not expose a licence field.

Raha/Jung, SEC, FinRule, BAF and GMSC are **not submitted** to the free endpoint. Existing uncertain upstream rights and BAF's NC-ND/NC-SA conflict are not bypassed. No private Avanade/Rabobank data is used. Independently reviewed natural DQ labels remain unavailable; generation on licensed metadata does not solve that scientific gate.

Technical validation can read a development-only subset of the already acquired UCI records **locally**. It removes targets, groups duplicate feature rows, exports only counts/row indices and does not send the records to Gemini. These local alerts are workload, not verified error precision. Original raw data and cache files remain ignored and read-only where applicable.
