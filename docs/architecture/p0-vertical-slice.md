# P0 vertical slice

The first deployed version is intentionally a controlled benchmark, not a claim
of camera intelligence or physical-energy measurement.

## Learning boundary

The shape generator uses a private semantic name only to rasterize an image on a
32 × 32 intensity retina with 2 × 2 subpixel edge sampling. Each presentation independently varies scale,
rotation, position, sensor noise, and occlusion. The learning engine receives
only the 1,024 retinal intensities and cannot access labels or symbolic shape
identifiers. The evaluator independently maps held-out retinal images to private
labels, hashes the model before and after evaluation, and reports whether it
changed the model.

## Structure

- Cells are adaptive feature prototypes.
- Organisms are small dynamic collections of cells.
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

## MVP limitations

- The resource ledger is a compute and memory proxy, not measured wattage.
- Colony synergy is deliberately simple and must be improved with multi-seed
  comparisons and stronger counterfactual attribution.
- The evaluator currently reports purity. Standard NMI and ARI belong to P1.
- GPT-5.6 curriculum and explanation calls, camera input, and physical energy
  measurements are P1+ work and are absent from this release.

## Public-session boundary

Each browser receives a persistent opaque session identifier and its own engine
instance. API learning operations require that identifier; an older client or a
different visitor cannot advance, reset, evaluate, or ablate another visitor's
ecosystem. The in-memory registry retains at most 64 recent sessions.
