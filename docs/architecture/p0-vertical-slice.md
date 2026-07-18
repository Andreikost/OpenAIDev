# P0 vertical slice

The first deployed version is intentionally a controlled benchmark, not a claim
of camera intelligence or physical-energy measurement.

## Learning boundary

The shape generator uses a private semantic name only to create synthetic
features. The learning engine receives feature vectors and cannot access labels.
The evaluator independently maps held-out vectors to private labels, hashes the
model before and after evaluation, and reports whether it changed the model.

## Structure

- Cells are adaptive feature prototypes.
- Organisms are small dynamic collections of cells.
- Colonies are persistent pairs of complementary mature organisms.
- The resource score is marginal unsupervised benefit minus active-structure
  proxy cost.
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
