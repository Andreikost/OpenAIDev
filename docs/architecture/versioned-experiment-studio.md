# Versioned Experiment Studio

## Product idea

ColonyMind keeps the submitted Build Week learner as an immutable scientific
reference and treats every later hypothesis as a derived experiment. A user can
run the GPT-5.6 Research Auditor, add a constraint in the experiment chat, and
create a reproducible version without editing or replacing the reference system.

## Immutable baseline

The baseline is identified by:

- ID `colonymind-build-week-baseline-v1`;
- Git commit `1e44699729e61450a62d6b42e0d32c3785a9eddf`;
- SHA-256 of `backend/app/core.py`;
- UI and API declarations that it is neither editable nor deletable.

`test_baseline_core_fingerprint_is_frozen` fails if a byte in the baseline
engine changes. The experiment implementation lives in separate modules and
creates a new `ColonyMindEngine` for every seed. It never passes an experiment
configuration into the baseline learner.

## Safe GPT-5.6 boundary

GPT-5.6 receives the cached Research Auditor result, the baseline manifest, an
optional parent version, and at most 1,200 characters of human instruction. It
returns a Pydantic Structured Output and has no tools or code execution path.

The allowlisted protocol contains only:

- experiment type: multi-seed replication, nuisance robustness, or learning curve;
- two to five unique seeds;
- 240 to 2,400 training steps per seed;
- eight to 24 external-evaluator samples per shape;
- baseline, rotation, noise, occlusion, or mixed nuisance profiles;
- bounded checkpoints for learning curves.

The product-level compute budget is at most 7,200 seed-steps per version. This
protects the shared VPS; it is not a cell, organism, colony, or learning-growth
ceiling inside ColonyMind.

## Execution and evidence

One background worker runs versions sequentially. Each independent engine starts
with zero learned structure. The frozen evaluator generates labeled samples only
after training and verifies its state hash before and after evaluation.

Every result reports:

- per-seed and aggregate purity;
- normalized mutual information (NMI);
- adjusted Rand index (ARI);
- community fragmentation;
- cells, organisms, colonies, memories, and micro-signatures;
- resource proxies with an explicit non-energy boundary;
- the baseline ID and commit used as the reference.

## Anonymous and authenticated modes

The browser generates an experiment workspace ID in memory and never stores it.
An anonymous refresh therefore opens a new empty version registry. Orphaned
anonymous registries are bounded and evicted from server memory. The baseline is
always available because it is not part of that registry.

Google login uses Google Identity Services in the browser. The backend verifies
the access token and its audience, then issues an app-specific signed session.
Authenticated experiment versions are owned by the Google subject and persisted
in PostgreSQL. Users can list, derive variants, execute, inspect, and delete only
their own versions. Deleting the baseline is rejected by both API and registry.

## API surface

- `GET /api/auth/config`, `POST /api/auth/google`, `GET /api/auth/me`
- `GET /api/experiments/baseline`
- `GET /api/experiments`
- `POST /api/experiments`
- `POST /api/experiments/{id}/run`
- `DELETE /api/experiments/{id}`

Experiment requests use the ordinary isolated learner session header plus a
separate ephemeral workspace header. An optional bearer token changes storage
from bounded memory to the authenticated PostgreSQL workspace.
