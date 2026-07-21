# GPT-5.6 Research Auditor

## Purpose

The Research Auditor turns ColonyMind's structured evidence into a concise,
scientifically conservative interpretation for judges and experimenters. It is
not part of the learner. GPT-5.6 cannot choose winners, update prototypes, create
cells, form colonies, consolidate memories, or access a mutation endpoint.

## Data boundary

The backend freezes a compact `colonymind-research-snapshot/v1` object containing:

- simulation seed, step, state hash, and the label-free training declaration;
- aggregate learning, population, cell, colony, memory, and micro-layer metrics;
- structural-event counts, hidden read-only evaluation, and Draw & Audit totals;
- the engine's heuristic recommendations and explicitly declared limitations.

The snapshot excludes raw retinal pixels, normalized drawings, cell prototypes,
mutable engine references, credentials, and full event histories. State hashes
are measured immediately before and after snapshot extraction. The OpenAI call
runs only after the engine lock is released and receives neither tools nor an
engine reference.

## OpenAI integration

The backend uses the OpenAI Python SDK, Responses API, `gpt-5.6-sol`, low
auditor reasoning, and Pydantic Structured Outputs. `store=false` is used for the request,
and a stable privacy-preserving safety identifier is derived by hashing the
opaque browser session ID. The API credential remains server-side.

The auditor has its own 120-second timeout and a bounded 3,000-token response.
It deliberately disables automatic SDK retries so one slow paid request cannot
turn into overlapping attempts beyond the reverse-proxy window. A per-session
cooldown, shared hourly allowance, concurrency limit, and state-hash cache
protect the public demo and its API credit. Failures return a retryable message;
the frozen snapshot and learner remain unchanged.

The validated response contains:

1. a judge-facing takeaway and conservative verdict;
2. observations with JSON-path evidence and separate interpretations;
3. scientific risks;
4. exactly three prioritized controlled experiments;
5. publication-readiness and resource-claim assessments.

The prompt explicitly prevents electrical-energy claims from compute proxies
and prevents synthetic-shape results from being presented as general vision.

## Cost and failure behavior

Audits are cached by requested model and frozen state hash, with a bounded cache
of 128 results. A repeated audit of an unchanged run reuses the existing result.
The downloadable performance report includes the cached audit for its matching
state hash; it never triggers a paid audit implicitly.
If the API key is absent, the endpoint returns a configuration error; if OpenAI
is unavailable or violates the output contract, the interface reports failure
without changing the learner.

## Verification

- Snapshot generation is tested as read-only and below a compact size boundary.
- Tests assert that raw retina and drawing pixels are absent.
- The API request has no `tools`, uses `store=false`, and requires the Pydantic
  response contract.
- A cached repeat does not invoke the model again.
