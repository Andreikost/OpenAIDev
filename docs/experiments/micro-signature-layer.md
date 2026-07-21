# Intermediate micro-signature experiment

Date: 2026-07-20  
Seed: `20260718`

## Problem observed

The step-47,064 report showed that capacity alone did not create useful concepts.
The system retained 6 organisms, 17 cells, 49 memories, and 745 recalls, but the
hidden purity was only 50%. In Draw & Audit it recognized 0 of 6 circles, 3 of 3
triangles, and 3 of 5 squares. One dominant organism responded to circles,
triangles, and squares, showing that the missing capability was representation,
not simply lifespan or population size.

## Hypothesis

Fine visual details should be information food for a label-free intermediate
population. Local micro-signatures should digest edge direction, curvature,
corners, contrast, and texture. Persistent coactivation should form colonies,
whose activity becomes the input to higher concept organisms. Familiar detail
must stop producing growth food.

## Implemented rule

1. A 64 × 64 unlabeled retina is smoothed and divided into 4 × 4 receptive fields.
2. Each field emits an eight-value local descriptor. Familiar descriptors update
   their nearest micro-signature; persistent residual descriptors create one.
3. Repeated simultaneous activation forms a micro-colony.
4. Global contour harmonics and radial alignment provide 16 rotation-tolerant
   values; hashed micro activity contributes another 16 values.
5. Concept organisms route on this 32-value intermediate representation.
6. Four compatible, persistently novel signatures can create a specialist.
   Familiar signatures create no new organism. No population, cell, colony, or
   micro-signature maximum is imposed.

Shape labels are absent from all six learning rules. They are used only after
training by the read-only evaluator.

## Explicit organism affinity map

The compressed 16-value micro-activity context remains the validated routing
input. In addition, every organism now records an explainability-only affinity
profile over the exact micro-signature IDs active when that organism wins.
Each value is an exponential moving estimate of
`P(micro-signature active | organism wins)` with rate `0.035`.

The explicit profile does not participate in routing, winner selection, cell
updates, growth, or memory consolidation. It therefore exposes organism-detail
relationships without perturbing the learning behavior validated below. The
public state and JSON report include every retained affinity and its update
count. In the 3D view, selecting an organism highlights meaningful affinities,
dims unrelated micro-signatures, and draws cross-layer links. The display
threshold is relative to that organism's strongest affinity and does not limit
what is stored or reported.

## Deterministic validation

| Step | Hidden purity (24) | Organisms | Cells | Concept colonies | Micro-signatures | Memories |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 240 | 100.0% | 5 | 7 | 2 | 31 | 1 |
| 2,400 | 100.0% | 9 | 15 | 4 | 56 | 15 |

An additional 300-sample held-out probe at step 2,400 reached 97.67% purity:

| Actual | Circle | Triangle | Square |
| --- | ---: | ---: | ---: |
| Circle | 98 | 2 | 0 |
| Triangle | 3 | 97 | 0 |
| Square | 2 | 0 | 98 |

This diagnostic used labels only to score the already-frozen assignments. The
live-state hash remained the read-only boundary for the built-in evaluation.

A five-seed check at step 240 produced hidden purities of `1.000`, `0.958`,
`1.000`, `1.000`, and `1.000` (mean `0.992`, minimum `0.958`). The learned
structure ranged from four to five organisms and 25 to 32 micro-signatures,
which is expected for an open-ended rather than fixed-width topology.

## Interpretation

The experiment supports the micro-colony hypothesis. Circle/square confusion
fell from complete circle failure in the supplied report to 98/100 correct for
each class in the larger probe. Growth remained demand-driven: several organisms
cover different render modes and transformations, while repeated patterns created
memories and 407 recalls rather than requiring a fixed three-organism topology.

These synthetic results validate the architecture mechanism, not general camera
vision. Multi-seed confidence intervals, natural contour datasets, measured CPU
time/memory, and learned rather than engineered invariance remain the next tests.
