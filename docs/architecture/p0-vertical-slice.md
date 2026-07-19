# P0 vertical slice

The first deployed version is intentionally a controlled benchmark, not a claim
of camera intelligence or physical-energy measurement.

## Learning boundary

The shape generator uses a private semantic name only to rasterize an image on a
64 × 64 intensity retina with 2 × 2 subpixel edge sampling. Presentations alternate between filled and outline-only stimuli and independently vary scale,
rotation, position, sensor noise, and occlusion. The learning engine receives
only the 4,096 retinal intensities and cannot access labels or symbolic shape
identifiers. The evaluator independently maps held-out retinal images to private
labels, hashes the model before and after evaluation, and reports whether it
changed the model.

The interactive drawing probe follows the same boundary. A visitor's 64 × 64
drawing is normalized and compared with the learned organism prototypes without
updating them. A separate geometric template auditor owns the circle, triangle,
and square labels, labels the drawing, maps the responding organism through
held-out samples, and reports agreement. Before/after hashes make this read-only
claim directly auditable in the interface.

## Performance report

Each browser session can download a versioned JSON report containing recent
loss values and resource proxies; aggregate and per-organism cell metrics;
organism population and lineage counts; colony formation, dissolution, and
synergy; structural adaptation totals and history; hidden evaluation; and all
Draw & Audit results recorded since the last reset. The report explicitly calls
these events structural adaptations rather than genetic mutations and adds
evidence-linked heuristic recommendations for the next experiment.

## Structure

- Cells are adaptive feature prototypes.
- Organisms are small dynamic collections of cells with three lifecycle states:
  `young`, `mature`, and `dormant`.
- Colonies are persistent pairs of complementary mature organisms.
- The resource score is marginal unsupervised benefit minus active-structure
  proxy cost.
- Retinal observations become temporary food patches in a deterministic 2-D
  information habitat. Organism activation steers movement toward a patch;
  low-activation organisms explore, and colony members balance foraging with
  cohesion. Therefore the canvas visualizes motor state produced by the learning
  engine rather than assigning fixed decorative positions.
- A structural review runs every twelve learning steps. It may add capacity for
  a persistent residual or an input vector sufficiently novel relative to the
  existing specializations. The decision uses only feature-vector distance;
  shape names are not available to the learner.

## P1 long-term memory lifecycle

The original short-lived population policy was unsuitable for learning because
it could erase a specialization before the system had enough evidence to judge
it. The current policy ages every resident organism on every global step, not
only the winning organism. Young organisms learn at full plasticity. After at
least 120 steps and eight wins they become mature and update more slowly, which
reduces catastrophic drift.

An unused mature organism becomes dormant only after 2,000 inactive steps.
Dormancy keeps its prototype and cells in resident memory while excluding it
from routine learning updates and active-compute proxies. A retinal input close
to its specialization reactivates it with temporarily elevated plasticity.

For each new stimulus, a cheap specialization comparison selects every organism
within a relevance margin of the best response. This committee has no fixed
member count. Only relevant organisms perform the more expensive cell-level
reconstruction; all other organisms remain resident and retrievable.

No organism can be archived during its first 5,000 lifetime steps. After that,
archival still requires all of the following evidence: long inactivity,
sustained negative value, a nearly duplicate resident specialization, and a
non-positive replay-buffer ablation. The JSON v4 report separates processing
from resident organisms/cells and records lifecycle state, age, wins,
reactivations, policy thresholds, and the archive registry.

## Open-ended information-food growth

There are no fixed maxima for organisms, cells, or colonies. Growth is instead
controlled by informational food: reconstruction residual above the digestion
threshold. A noisy sample cannot create permanent structure. Residuals must
form a repeated, label-free similarity cluster before they can create a cell or
organism.

Cells compete locally inside the responding organism. Only its strongest cell
updates on a sample, allowing other cells to retain distinct specializations.
When repeated low-residual evidence shows that an organism or colony has fully
digested a visual regime, the group creates a persistent unlabeled memory
engram. A recalled memory sets structural food to zero, so familiar information
cannot grow more cells or organisms. The external evaluator may later associate
these memories with semantic shapes, but shape names never enter learning.

## MVP limitations

- The resource ledger is a compute and memory proxy, not measured wattage.
- Colony synergy is deliberately simple and must be improved with multi-seed
  comparisons and stronger counterfactual attribution.
- The evaluator currently reports purity. Standard NMI and ARI belong to P1.
- The lifecycle prevents premature forgetting, but it does not by itself create
  rotation/scale-invariant representations; that remains the next learning-quality experiment.
- GPT-5.6 curriculum and explanation calls, camera input, and physical energy
  measurements are P1+ work and are absent from this release.

## Public-session boundary

Each browser receives a persistent opaque session identifier and its own engine
instance. API learning operations require that identifier; an older client or a
different visitor cannot advance, reset, evaluate, or ablate another visitor's
ecosystem. The in-memory registry retains at most 64 recent sessions.
