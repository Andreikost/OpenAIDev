# P1 lifecycle benchmark

Date: 2026-07-19  
Seed: `20260718`

## Why this iteration exists

The downloaded P0 report at step 30,732 showed 101 organism births and 98
archives. Only three organisms survived. That turnover was incompatible with
long-term learning because specializations could disappear before accumulating
enough evidence.

## Implemented policy

- Every resident ages on every global step, including non-winners.
- Young organisms become mature after 120 steps and eight wins.
- Mature prototypes use lower plasticity to reduce drift.
- Dormancy retains memory without routine prototype updates.
- Similar inputs can reactivate dormant memory.
- The first 5,000 lifetime steps are protected from archival.
- Later archival requires long inactivity, sustained low value, a redundant
  specialization, and non-positive replay-buffer ablation.
- A response committee preselects at most four organisms for costly cell-level
  processing while all organisms remain resident and retrievable.

## Deterministic 6,000-step result

| Metric | P1 lifecycle result |
| --- | ---: |
| Organisms created | 8 |
| Resident organisms | 8 |
| Organisms in current response committee | 4 |
| Organisms archived | 0 |
| Mature / young / dormant | 7 / 1 / 0 |
| Resident / active cells | 64 / 32 |
| Colonies | 3 |
| Current / recent mean loss | 0.04421 / 0.04145 |
| Hidden-label purity | 50.0% |
| Resource score | -0.1486 |
| State hash | `345f841304ae` |

The same lifecycle without committee selection produced 64 active cells and a
resource score of -0.4796 at 6,000 steps. The committee therefore reduced the
active cell set by 50% and improved this compute proxy by about 69%, while
retaining all eight organism memories and the same 50% hidden-label purity.

## Interpretation

This iteration fixes premature forgetting; it does not yet prove robust shape
concept learning. The purity increase from the prior downloaded run (41.7%) to
50.0% is encouraging but remains too low for the final claim, and the runs have
different durations. The next controlled experiment should add an invariant
representation objective for rotation, scale, translation, fill/outline, and
noise, then compare multiple identical seeds and curricula.

