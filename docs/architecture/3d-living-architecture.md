# 3D living architecture

Date: 2026-07-21

This release changes only the visual projection of ColonyMind. The backend
learning, growth, lifecycle, memory, and evaluation algorithms are unchanged.

## Visual mapping

Every rendered object comes from the existing state contract:

- Retinal information patches descend through the field as octahedral food.
- Micro-signatures occupy the lower amber layer. Persistent coactivation draws
  the real micro-colony membership links.
- Each organism is a luminous core located from its live `x`, `y`, energy, age,
  and lifecycle values.
- Every resident cell is rendered individually around its owning organism. The
  lines show structural attachment inside that organism; they do not claim to
  be learned biological synapses.
- Concept colonies use their real member lists to create connections and a
  translucent shared membrane.
- Consolidated memories appear as green engram rings above the organisms that
  own them. Stability and recall count affect their size and luminosity.

No simulated cell, organism, colony, or memory is added for visual effect. The
scene rebuilds from the API state after every training batch, so births, growth,
dormancy, colony formation, digestion, and memory consolidation change the same
3D field the visitor is exploring.

## Interaction

- Drag or touch to rotate.
- Use the wheel or pinch gesture to zoom.
- Click an organism or one of its cells to open the existing inspector.
- Focus the selected organism, reset the camera, pause automatic orbit, or enter
  full-screen presentation mode.

The renderer caps device pixel ratio for predictable GPU cost but does not cap
the learning topology. The 2D retina, metrics, inspector, Draw & Audit lab, and
JSON report remain unchanged.
