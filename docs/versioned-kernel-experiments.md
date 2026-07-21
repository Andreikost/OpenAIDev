# Versioned kernel experiments

ColonyMind keeps the submitted Build Week learner in `backend/app/core.py` as an immutable reference. Its normalized SHA-256 remains the deployment gate. Experimental changes never overwrite that file or the live baseline engine.

## Isolation model

Each version starts from zero learned state in a new `VariantColonyMindEngine`. The version records:

- the immutable baseline core hash;
- the experimental runner source hash;
- a canonical hash of the variant specification;
- seeds, requested and actual training steps, checkpoints, shapes, and nuisance profile;
- every applied parameter override;
- a declaration that generated code was not executed.

GPT-5.6 produces a structured `ExperimentProposal`, not source code. Pydantic rejects extra fields. The only learning-policy changes it may request are bounded overrides for organism and cell birth novelty, digestion error, memory evidence, micro-detail novelty and support, intermediate birth novelty, and replay capacity.

Two reviewed algorithmic mechanisms are also available: `adaptive_novelty_schedule`, which progressively refines novelty sensitivity, and `memory_gated_growth`, which raises growth thresholds as persistent memories accumulate. They are implemented locally in the experimental runner and cannot be replaced with generated logic.

The only supported experimental shapes are circle, triangle, square, pentagon, star, and cross. The three baseline shapes are always retained as controls. Shape names are private to the generator and frozen evaluator; training still receives retinal intensity matrices without semantic labels.

## True step accounting

The baseline engine deliberately accepts at most 240 steps per call. The experiment runner therefore advances in verified chunks until `engine.step_count` equals the requested checkpoint. Each run stores both `requestedTrainingSteps` and `actualTrainingSteps`; an executable criterion fails if they differ.

## Matched controls

When a version changes a learning-policy parameter, the executor also runs a matched control with:

- identical seeds;
- identical shape vocabulary;
- identical training steps and nuisance profile;
- identical evaluator sample counts;
- the unmodified baseline learning policy.

The experimental runner uses a dedicated stimulus RNG, separate from structural randomness. Consequently, a birth or mutation in one arm cannot shift the later retinal sequence; both arms receive identical stimuli for a given seed.

The result reports deltas for clustering, structure, and resource proxies. New-shape-only versions use the baseline policy copy directly and therefore do not duplicate an identical control arm.

## Machine-verifiable criteria

Natural-language proposal criteria are preregistration notes, not automatic successes. After execution, the server independently verifies:

1. every engine reached the requested step;
2. the required fraction of seeds passed the declared purity, NMI, ARI, and fragmentation gate;
3. every shape received the declared balanced evaluator sample count;
4. evaluator hashes prove that evaluation did not modify learned state.

The UI displays `passed`, `failed`, or `not measured`; it no longer adds unconditional checkmarks.

## Version audits and descendants

A completed version can be sent to GPT-5.6 for an aggregate-only research audit. The snapshot excludes raw retinal pixels, prototypes, mutable engine references, and write endpoints. A child version may derive from that result audit, allowing a chain such as:

`baseline → multi-seed replication → extended shapes → bounded kernel tuning → nuisance robustness`

Authenticated versions and their audits persist in PostgreSQL. Anonymous versions remain session-ephemeral.
