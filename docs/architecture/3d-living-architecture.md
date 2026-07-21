# 3D living architecture

Date: 2026-07-21

This release changes only the visual projection of ColonyMind. The backend
learning, growth, lifecycle, memory, and evaluation algorithms are unchanged.

## Visual mapping

Every rendered object comes from the existing state contract:

- Retinal information patches descend through the field as octahedral food.
- Micro-signatures occupy the lower amber layer. Persistent coactivation draws
  the real micro-colony membership links.
- Each organism begins as a rotating double-helix seed, buds its resident cells,
  weaves them into branching tissue, and only then forms a faint membrane. The
  sequence keeps its visual birth time across API refreshes instead of making a
  finished sphere appear on every snapshot. A closed membrane is withheld until
  at least three resident cells provide enough tissue to enclose.
- Every resident cell is rendered individually in a deterministic branching
  topology around its owning organism. Cell count, activation, energy, organism
  position, and lifecycle still come exclusively from the live state. The DNA
  helix expresses lineage as a visual metaphor; it does not claim that the
  backend uses a literal genetic operator.
- Each cell uses a translucent, irregular membrane around a luminous nucleus.
  Its breathing amplitude follows live activation. Tissue grows in curved
  segments from parent to child, and traveling light pulses make the active
  attachment legible; these are presentation cues, not claimed biological
  synapses.
- Multicellular organisms use a low-opacity irregular envelope so their cells
  and tissue remain visible through the organism boundary.
- Live `x`, `y` coordinates pass through a monotonic square-root presentation
  lens. This preserves direction and ordering while separating near-center
  organisms enough to inspect their cells; exact coordinates remain available
  in state and reports.
- Concept colonies use their real member lists to create connections and an
  orbit ring. This avoids covering the cellular topology with overlapping
  spherical shells.
- Consolidated memories appear as a distributed green engram constellation
  above the organisms that own them. Stability and recall count affect node
  size and luminosity. Only sampled anchor threads are drawn, preventing large
  memory populations from becoming stacked opaque rings.

No simulated cell, organism, colony, or memory is added for visual effect. The
scene rebuilds from the API state after every training batch while retaining a
presentation-only first-seen registry. Births, cell additions, tissue growth,
dormancy, colony formation, digestion, and memory consolidation therefore
change the same continuous 3D field the visitor is exploring.

## Interaction

- Drag or touch to rotate.
- Use the wheel or pinch gesture to zoom.
- Click an organism or one of its cells to open the existing inspector.
- Focus the selected organism, reset the camera, pause automatic orbit, or enter
  full-screen presentation mode.

The renderer caps device pixel ratio for predictable GPU cost but does not cap
the learning topology. The 2D retina, metrics, inspector, Draw & Audit lab, and
JSON report remain unchanged.
