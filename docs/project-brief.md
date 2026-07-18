# ColonyMind project brief

## One-line pitch

ColonyMind is a self-organizing vision architecture that grows neural cells
into small organism networks and forms colonies only when cooperation improves
learning more than it costs.

## The problem

Most vision systems begin with a fixed architecture and spend a broadly fixed
computational budget on each input. ColonyMind explores whether a visual learner
can allocate structure dynamically: grow where persistent information demand
exists, reuse specialists, route selectively, and prune capacity that no longer
earns its cost.

## Why basic shapes

Circles, triangles, and squares are the first controlled benchmark. Their
simplicity makes it possible to inspect whether a cell learns curves, corners,
symmetry, closure, rotation, or another useful visual regularity. Training uses
no class labels. Hidden labels are revealed only during read-only evaluation.

## Hierarchy

1. A cell is an adaptive visual feature unit.
2. An organism is a small dynamic neural expert made of cells and synapses.
3. A colony is a persistent sparse ensemble of complementary organisms.
4. The ecosystem routes finite information opportunities according to expected
   learning value and resource cost.

## Resource objective

Every component receives credit for measurable marginal loss reduction and
transfer value, then pays for active cells, synapses, communication, memory,
and compute proxies. The MVP reports a resource proxy, not physical energy in
watts. Hardware energy claims require a later controlled measurement campaign.

## Competition story

The memorable demo begins at zero learned structure, shows the first cells and
organisms emerging, advances through a disclosed deterministic checkpoint,
classifies a hand-drawn transformed shape by learned community, reveals the
hidden label, and ablates one organism to show its causal contribution.

GPT-5.6 compiles a safe curriculum from natural language and explains bounded
structured evidence. It does not train the model or access hidden labels.

## Initial success criteria

- Unlabeled training and read-only hidden evaluation are technically isolated.
- The same seed and step count produce the same state hash at every UI speed.
- A colony persists only when joint value exceeds individual value plus cost.
- Fixed, single-organism, and colony variants can be compared on matched data.
- The hosted experience is clear, reproducible, and usable without login.
