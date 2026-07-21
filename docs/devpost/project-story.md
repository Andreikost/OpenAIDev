## Inspiration

Most vision systems use a fixed architecture and spend roughly the same
computational budget on every image or video frame.

ColonyMind explores another path: an AI architecture that grows only when new
visual information justifies the cost, reuses existing specialists when
possible, and removes structures that no longer contribute.

Basic shapes are our wind tunnel, not the destination. Circles, triangles, and
squares give us a transparent first environment where every structural decision
can be observed, tested, and explained.

## What it does

ColonyMind is a self-organizing vision architecture that earns every unit of
computation it uses.

It receives visual information without class labels. Instead of starting with
a large fixed neural network, it grows neural cells, forms small organism
networks, and assembles colonies only when cooperation improves learning more
than it costs.

Users can watch cells emerge, inspect organism specialization, observe
persistent colonies, and reveal hidden-label evaluation only after training.
They can then freeze the evidence and ask an external GPT-5.6 Research Auditor
to identify findings, scientific risks, and the next controlled experiments.

## Why shapes first

A triangle is simple enough to inspect. If ColonyMind creates capacity for
corners, closure, or rotation-invariant structure, we can show why it happened.
This controlled benchmark gives us a reliable foundation before moving toward
complex visual patterns and eventually camera-based perception.

## How we built it

ColonyMind combines a React and TypeScript visual experience with a deterministic
Python and NumPy learning engine. The P0 system learns through feature-vector
reconstruction, dynamic topology, and a resource ledger that compares learning
benefit with structural cost. Its structural review can add capacity for a
persistent residual or a sufficiently novel unlabeled visual regime.

Codex supported architecture, implementation, testing, visualization,
documentation, and deployment throughout Build Week. GPT-5.6 Sol powers a
functional external Research Auditor through the Responses API and Structured
Outputs. It sees only aggregate metrics and declared limitations, returns a
validated research report, and has no tools or write access to the learner.

## Challenges we ran into

The hardest challenge is making the biological inspiration computationally
meaningful. A colony cannot be decoration: it must improve learning, robustness,
or efficiency after communication cost.

We also need strict isolation between unlabeled training and hidden ground
truth, deterministic structural growth, stable colony identity, and honest
resource metrics that do not confuse a compute proxy with electrical energy.

## Accomplishments that we're proud of

The intermediate micro-signature layer corrected the original circle/square
failure. In our checked-in five-seed benchmark, every seed trained for 240
steps and received a balanced frozen evaluation of 72 held-out samples. Purity
was 1.000 for all five seeds, while mean NMI was 0.9699, mean ARI was 0.9641,
and mean fragmentation was 1.2. Evaluator state hashes were preserved for every
run. These are controlled synthetic results, not a camera-vision claim, and the
machine-readable evidence is included in the repository.

We also built a working zero-to-colony learning journey, hidden-label read-only
evaluation, Draw & Audit lab, counterfactual organism ablation, downloadable
evidence report, interactive 3D architecture, and GPT-5.6 scientific audit with
an explicit hash-verified read-only boundary.

## What we learned

Bio-inspired design becomes useful when every metaphor maps to a measurable
mechanism. Food represents learnable information, energy represents marginal
benefit minus cost, organisms are small neural experts, and colonies represent
functional cooperation.

We also learned that a compelling visualization is not evidence by itself.
Claims about specialization or efficiency require controls, ablations, multiple
seeds, reproducible state, and explicit limitations.

## What's next for ColonyMind

The first milestone is circles, triangles, and squares under rotation, noise,
occlusion, and hand-drawn variation. Later phases can introduce composite
patterns, textures, natural image patches, temporal novelty, and opt-in camera
streams with privacy-preserving local preprocessing.
