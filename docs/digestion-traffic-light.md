# Digestion traffic light

The traffic light is a read-only interpretation of aggregate learning metrics. It does not write to the learner, alter its lifecycle, or claim that a green state proves generalization.

## Meaning

- **Red — Hungry / discovering:** the stream is still recruiting structure and no persistent memory has been consolidated.
- **Amber — Digesting / consolidating:** memories exist, but the recent evidence window is incomplete or residual novelty and structural growth remain.
- **Green — Current stream digested:** over a recent, multi-batch window, mean residual loss is controlled, fine-detail food is low on average, persistent memories exist, and structural recruitment is nearly flat.

Green means ecological saturation on the current unlabeled stream. The hidden-label evaluator and GPT research auditor remain the independent checks for category alignment, robustness, and generalization.

## Evidence window and thresholds

The frontend retains up to 40 aggregate snapshots and evaluates the latest 288 steps. At least three snapshots spanning 192 steps are required before green is possible. Structural growth is a weighted, presentation-only indicator built from changes in resident cells, resident organisms, micro-signatures, and active colonies per 96 steps.

The current calibration requires:

- at least 480 total learning steps;
- at least three consolidated memories;
- mean residual loss no greater than `0.061`;
- mean fine-detail food no greater than `0.38`;
- structural growth no greater than `0.75` weighted units per 96 steps.

These values were calibrated against seed `20260718`. In the reference run, step 240 had one memory and low instantaneous loss but still-changing detail food; it correctly remained amber. The evidence stabilized near step 960, where the recent structure changed by only one micro-signature and no new cells or organisms over 192 steps.

Because history is kept only in the browser, a refresh intentionally returns the indicator to amber while it rebuilds its observation window. This does not reset or modify the learner.

## Ecological saturation score

The displayed percentage is an explanatory composite of memory maturity, rolling mean loss, rolling fine-detail food, and recent structural stability. It is a dashboard score, not a probability, accuracy, or physical-energy measurement.
