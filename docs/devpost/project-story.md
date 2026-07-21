## Inspiration

Most visual learners begin with their architecture already decided: layers,
width, and capacity are chosen before the first image arrives. **ColonyMind asks
a different question: what if a learner had to earn new structure from the
information it could not yet explain?**

Nature gave us a useful design language. Unfamiliar information behaves like
food. Cells become small adaptive units. Cells form organism-like local experts.
Useful organisms cooperate as colonies, and familiar structure consolidates
into memory. These are functional software analogies, not claims that the system
is literally alive.

Circles, triangles, and squares are our wind tunnel, not our destination. They
create a controlled setting where growth, specialization, mistakes, and memory
can be inspected before moving toward complex visual patterns.

## What it does

ColonyMind is an **inspectable, label-free, self-structuring visual learner**.
Shapes enter through a 64 x 64 retina with changes in rotation, scale, position,
noise, occlusion, and filled or outline rendering. The learner never receives a
shape name.

Residual information acts as food. Persistent novelty can recruit cells, form
small organism networks, activate fine-detail micro-signatures, and create
colonies when cooperation is useful. Familiar input is consolidated into
persistent memory, reducing the pressure to keep growing. A red-amber-green
digestion indicator makes that process understandable without pretending that
green means general intelligence.

Users can rotate and zoom the live 3D architecture, inspect one organism and its
lineage, draw a new shape in **Draw & Audit**, run a frozen hidden-label
evaluation, download a structured evidence report, and ask GPT-5.6 to challenge
the experiment.

## How we built it

The learning core is a deterministic Python and NumPy engine exposed through
FastAPI. A React, TypeScript, and Three.js interface renders the engine's live
state as retina, cells, organisms, tissue, colonies, micro-signatures, and
memory. The visualization is not a prerecorded simulation layered over a
classifier.

Codex accelerated architecture, implementation, tests, visualization,
scientific documentation, evidence analysis, and VPS deployment throughout
Build Week. We used it as an engineering collaborator while retaining the key
scientific and product decisions: long-lived organisms, demand-driven growth,
the intermediate micro-signature layer, the resource ledger, and an immutable
baseline.

GPT-5.6 Sol powers the functional **Research Auditor** through the OpenAI
Responses API and Structured Outputs. It receives only a frozen aggregate
snapshot: metrics, structural counts, evaluation evidence, and declared
limitations. It receives no raw retinal pixels, cell prototypes, tools, mutable
engine reference, or learning endpoint. Before and after hashes verify that the
audit did not modify the learner.

The **Versioned Experiment Studio** converts an auditor proposal plus optional
human instructions into a schema-validated, allowlisted protocol. Each version
runs in a fresh isolated engine. Baseline v1 remains locked, and no
GPT-generated code is executed.

## Challenges we ran into

Our first organisms died too quickly to accumulate useful knowledge, so we
introduced long-lived resident organisms whose survival depends on sustained
learning contribution. The original retina was too coarse, so we increased it
to 64 x 64 and added filled and outline stimuli.

The most revealing failure was that circles were confused with squares. Global
shape information was not enough. We added an intermediate layer of local edge
and curvature **micro-signatures**, allowing fine details to become food for
specialists before they were composed into higher-level organisms and colonies.

The broader challenge was scientific honesty. A beautiful biological metaphor
is not evidence. We had to isolate labels, preserve deterministic state, test
multiple seeds, control fragmentation, and distinguish an engineering resource
proxy from measured FLOPs, memory, electrical energy, or carbon savings.

## Accomplishments that we're proud of

The micro-signature layer corrected the original circle/square failure and made
the learning process substantially more stable. In our checked-in five-seed
benchmark, every seed trained for 240 steps and was evaluated on 72 balanced
held-out samples. **Purity was 1.000 across all five seeds, mean NMI was 0.9699,
mean ARI was 0.9641, and mean fragmentation was 1.2.** Every evaluator state
hash was preserved.

We are equally proud of the boundaries around those numbers. They are evidence
for organization on a controlled three-shape benchmark, not proof of natural
image recognition, camera generalization, or superior energy efficiency.

The project also delivers a zero-to-colony learning journey, interactive 3D
inspection, hidden-label read-only evaluation, Draw & Audit, organism ablation,
downloadable JSON evidence, a GPT-5.6 scientific audit, and reproducible
versioned experiments without putting the baseline at risk.

## What we learned

Bio-inspired design becomes useful only when every metaphor maps to an
observable mechanism. Food must correspond to residual information. Growth must
respond to persistent novelty. Cooperation must earn its cost. Memory must
reduce repeated adaptation on familiar input.

We also learned that **inspectability and evidence must evolve together**. A
living 3D visualization can explain what the system is doing, but controlled
evaluations, ablations, multiple seeds, state hashes, and explicit limitations
are what make the explanation credible.

## What's next for ColonyMind

The next experiments will compare ColonyMind with matched fixed-capacity and
label-free baselines while directly measuring wall-clock time, peak memory,
compute utilization, and physical energy. We will also test nuisance robustness,
unseen shapes, composite forms, textures, and natural image patches.

Only after those controlled steps will we extend the retina toward opt-in camera
streams with privacy-preserving local preprocessing. The long-term goal is not
another large fixed vision model. It is a transparent learning architecture
that can restructure itself, preserve what it knows, and justify the resources
it asks to use.
