from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np


SHAPES = ("circle", "triangle", "square")
COLORS = ("#64d9ff", "#b38cff", "#ffb45c", "#77e39e", "#f486c4")


@dataclass
class Cell:
    id: str
    organism_id: str
    prototype: list[float]
    energy: float = 0.52
    utility: float = 0.0
    activation: float = 0.0
    age_steps: int = 0
    redundancy: float = 0.0


@dataclass
class Organism:
    id: str
    lineage: str
    color: str
    cells: list[str] = field(default_factory=list)
    energy: float = 0.58
    utility: float = 0.0
    specialization: list[float] = field(default_factory=list)
    colony_id: str | None = None
    age_steps: int = 0
    contribution: float = 0.0


@dataclass
class Colony:
    id: str
    member_ids: list[str]
    core_members: list[str]
    energy: float = 0.0
    state: str = "confirmed"
    formed_step: int = 0
    synergy: float = 0.0


class ColonyMindEngine:
    """Small deterministic, label-free visual learner for the Build Week MVP.

    Shape names determine synthetic pixels only. The engine receives feature vectors
    and never accesses labels. A separate evaluator owns the shape-name mapping.
    """

    vector_size = 16

    def __init__(self, seed: int = 20260718) -> None:
        self.reset(seed)

    def reset(self, seed: int | None = None) -> None:
        self.seed = self.seed if seed is None and hasattr(self, "seed") else (seed or 20260718)
        self.rng = random.Random(self.seed)
        self.step_count = 0
        self.cells: dict[str, Cell] = {}
        self.organisms: dict[str, Organism] = {}
        self.colonies: dict[str, Colony] = {}
        self.events: list[dict[str, Any]] = []
        self.loss_history: list[float] = []
        self.current_stimulus: dict[str, Any] | None = None
        self.previous_loss: float | None = None
        self.high_residual_streak = 0
        self._ids = {"cell": 0, "organism": 0, "colony": 0, "sample": 0}
        self._event("SESSION_STARTED", "ecosystem", ["ZERO_LEARNED_STRUCTURE"], {})

    def _next_id(self, kind: str) -> str:
        self._ids[kind] += 1
        prefix = {"cell": "cell", "organism": "org", "colony": "col", "sample": "sample"}[kind]
        return f"{prefix}-{self._ids[kind]:03d}"

    def _event(self, kind: str, entity_id: str, reasons: list[str], metrics: dict[str, float]) -> None:
        self.events.append({
            "step": self.step_count,
            "kind": kind,
            "entityId": entity_id,
            "reasons": reasons,
            "metrics": {key: round(value, 5) for key, value in metrics.items()},
        })
        self.events = self.events[-24:]

    def _vector_for(
        self,
        shape: str,
        rotation: float,
        noise: float,
        occlusion: float,
        rng: random.Random | None = None,
    ) -> np.ndarray:
        source_rng = rng or self.rng
        base = {
            "circle": [0.96, 0.12, 0.08, 0.87, 0.91, 0.18, 0.13, 0.82, 0.92, 0.14, 0.10, 0.85, 0.89, 0.15, 0.11, 0.83],
            "triangle": [0.14, 0.93, 0.81, 0.22, 0.16, 0.88, 0.76, 0.27, 0.13, 0.90, 0.80, 0.21, 0.18, 0.86, 0.74, 0.29],
            "square": [0.71, 0.78, 0.19, 0.28, 0.68, 0.81, 0.22, 0.25, 0.73, 0.76, 0.18, 0.30, 0.70, 0.80, 0.21, 0.27],
        }[shape]
        vector = np.asarray(base, dtype=np.float64)
        phase = math.sin(rotation) * 0.045
        vector = vector + np.asarray([phase if index % 2 else -phase for index in range(self.vector_size)])
        vector = vector + np.asarray([source_rng.uniform(-noise, noise) for _ in range(self.vector_size)])
        if occlusion > 0:
            start = source_rng.randrange(0, self.vector_size // 2) * 2
            vector[start : start + 2] *= 1.0 - occlusion
        return np.clip(vector, 0.0, 1.0)

    def _sample(self) -> tuple[np.ndarray, dict[str, Any], str]:
        shape = self.rng.choice(SHAPES)
        rotation = self.rng.uniform(-math.pi, math.pi)
        noise = self.rng.uniform(0.005, 0.065)
        occlusion = self.rng.choice((0.0, 0.0, 0.12, 0.22))
        vector = self._vector_for(shape, rotation, noise, occlusion)
        sample_id = self._next_id("sample")
        public = {
            "id": sample_id,
            "rotation": round(rotation, 3),
            "noise": round(noise, 3),
            "occlusion": occlusion,
            "visualShape": shape,
        }
        # The label is intentionally returned separately and never passed to learning.
        return vector, public, shape

    def _create_organism(self, prototype: np.ndarray, reason: str, parent: Organism | None = None) -> Organism:
        organism_id = self._next_id("organism")
        organism = Organism(
            id=organism_id,
            lineage=parent.lineage if parent else organism_id,
            color=COLORS[(self._ids["organism"] - 1) % len(COLORS)],
            specialization=prototype.round(4).tolist(),
            energy=0.54 if parent else 0.62,
        )
        self.organisms[organism_id] = organism
        self._create_cell(organism, prototype, reason)
        self._event("ORGANISM_BIRTH", organism_id, [reason], {"organismEnergy": organism.energy})
        return organism

    def _create_cell(self, organism: Organism, prototype: np.ndarray, reason: str) -> Cell:
        cell_id = self._next_id("cell")
        cell = Cell(id=cell_id, organism_id=organism.id, prototype=prototype.round(4).tolist())
        self.cells[cell_id] = cell
        organism.cells.append(cell_id)
        self._event("CELL_BIRTH", cell_id, [reason], {"cellEnergy": cell.energy})
        return cell

    @staticmethod
    def _distance(vector: np.ndarray, prototype: list[float]) -> float:
        return float(np.mean((vector - np.asarray(prototype)) ** 2))

    def _organism_response(self, organism: Organism, vector: np.ndarray) -> tuple[float, np.ndarray, list[tuple[Cell, float]]]:
        scored: list[tuple[Cell, float]] = []
        for cell_id in organism.cells:
            cell = self.cells[cell_id]
            score = math.exp(-self._distance(vector, cell.prototype) / 0.06) * (0.62 + 0.38 * min(1.0, cell.energy))
            scored.append((cell, score))
        total = sum(score for _, score in scored) or 1.0
        activation = max(score for _, score in scored) if scored else 0.0
        reconstruction = sum(np.asarray(cell.prototype) * score for cell, score in scored) / total
        return activation, reconstruction, scored

    def _create_colony_if_useful(self) -> None:
        unassigned = [org for org in self.organisms.values() if org.colony_id is None and org.age_steps >= 8]
        if len(unassigned) < 2:
            return
        first, second = sorted(unassigned, key=lambda org: org.utility, reverse=True)[:2]
        diversity = self._distance(np.asarray(first.specialization), second.specialization)
        synergy = max(0.0, diversity * 1.8 + first.contribution + second.contribution - 0.06)
        if diversity < 0.014 or synergy < 0.035:
            return
        colony = Colony(
            id=self._next_id("colony"),
            member_ids=[first.id, second.id],
            core_members=[first.id, second.id],
            energy=first.energy + second.energy,
            formed_step=self.step_count,
            synergy=synergy,
        )
        self.colonies[colony.id] = colony
        first.colony_id = colony.id
        second.colony_id = colony.id
        self._event("COLONY_FORMED", colony.id, ["PERSISTENT_COMPLEMENTARY_SPECIALIZATION", "POSITIVE_JOINT_VALUE"], {"synergy": synergy, "diversity": diversity})

    def _structural_review(self, vector: np.ndarray, loss: float) -> None:
        best = max(self.organisms.values(), key=lambda org: org.utility, default=None)
        novelty = min(
            (self._distance(vector, organism.specialization) for organism in self.organisms.values()),
            default=1.0,
        )
        if loss > 0.052:
            self.high_residual_streak += 1
        else:
            self.high_residual_streak = max(0, self.high_residual_streak - 1)
        novel_regime = novelty > 0.045 and len(self.organisms) < 3 and self.step_count >= 24
        if (self.high_residual_streak >= 3 or novel_regime) and len(self.organisms) < 8:
            reason = "NOVEL_UNLABELED_VISUAL_REGIME" if novel_regime else "PERSISTENT_UNSERVED_VISUAL_RESIDUAL"
            self._create_organism(vector, reason, best)
            self.high_residual_streak = 0
        else:
            if best and loss > 0.025 and len(best.cells) < 8:
                self._create_cell(best, vector, "LOCAL_RESIDUAL_SPECIALIZATION")
        self._create_colony_if_useful()
        for organism in list(self.organisms.values()):
            if organism.age_steps > 40 and organism.utility < -0.012 and len(self.organisms) > 1:
                for cell_id in organism.cells:
                    self.cells.pop(cell_id, None)
                self.organisms.pop(organism.id, None)
                self._event("ORGANISM_ARCHIVED", organism.id, ["PERSISTENT_NEGATIVE_MARGINAL_VALUE"], {"utility": organism.utility})
                break

    def step(self, count: int = 1) -> dict[str, Any]:
        for _ in range(max(1, min(count, 240))):
            self.step_count += 1
            vector, public, _label = self._sample()
            self.current_stimulus = public
            if not self.organisms:
                self._create_organism(vector, "FIRST_UNLABELED_STIMULUS")
                self.loss_history.append(0.0)
                continue
            responses = [(org, *self._organism_response(org, vector)[:2]) for org in self.organisms.values()]
            responses.sort(key=lambda row: row[1], reverse=True)
            winner, winner_activation, reconstruction = responses[0]
            error = float(np.mean((vector - reconstruction) ** 2))
            previous = self.previous_loss if self.previous_loss is not None else error
            improvement = max(-0.08, min(0.08, previous - error))
            self.previous_loss = error
            active_cost = 0.0018 * len(winner.cells) + 0.0008 * len(self.cells)
            communication_cost = 0.003 if winner.colony_id else 0.0
            winner.contribution = max(0.0, improvement + 0.12 * error)
            winner.utility = 0.84 * winner.utility + 0.16 * (winner.contribution - active_cost - communication_cost)
            winner.energy = min(1.5, max(0.0, winner.energy + winner.utility * 0.11))
            winner.age_steps += 1
            for cell_id in winner.cells:
                cell = self.cells[cell_id]
                activation = math.exp(-self._distance(vector, cell.prototype) / 0.06)
                cell.activation = activation
                cell.age_steps += 1
                learning_rate = 0.018 + 0.055 * activation
                prototype = np.asarray(cell.prototype)
                prototype = prototype + learning_rate * (vector - prototype)
                cell.prototype = np.clip(prototype, 0.0, 1.0).round(4).tolist()
                cell.utility = 0.84 * cell.utility + 0.16 * (winner.contribution * activation - 0.0015)
                cell.energy = min(1.35, max(0.0, cell.energy + cell.utility * 0.09))
            winner.specialization = np.mean([self.cells[cell_id].prototype for cell_id in winner.cells], axis=0).round(4).tolist()
            if winner.colony_id and winner.colony_id in self.colonies:
                colony = self.colonies[winner.colony_id]
                colony.energy = sum(self.organisms[member].energy for member in colony.member_ids if member in self.organisms)
                colony.synergy = 0.86 * colony.synergy + 0.14 * max(0.0, winner.contribution - communication_cost)
            self.loss_history.append(error)
            self.loss_history = self.loss_history[-120:]
            if self.step_count % 12 == 0:
                self._structural_review(vector, error)
        return self.state()

    def _state_payload(self) -> dict[str, Any]:
        organisms = []
        for index, organism in enumerate(self.organisms.values()):
            angle = index * (math.pi * 2 / max(1, len(self.organisms)))
            organisms.append({
                "id": organism.id,
                "lineage": organism.lineage,
                "color": organism.color,
                "cellIds": organism.cells,
                "energy": round(organism.energy, 3),
                "utility": round(organism.utility, 4),
                "contribution": round(organism.contribution, 4),
                "colonyId": organism.colony_id,
                "ageSteps": organism.age_steps,
                "x": round(50 + math.cos(angle) * 28, 2),
                "y": round(50 + math.sin(angle) * 24, 2),
            })
        return {
            "seed": self.seed,
            "stepCount": self.step_count,
            "stateHash": self.state_hash(),
            "currentStimulus": self.current_stimulus,
            "metrics": {
                "loss": round(self.loss_history[-1] if self.loss_history else 0.0, 5),
                "meanLoss": round(float(np.mean(self.loss_history)) if self.loss_history else 0.0, 5),
                "activeCells": len(self.cells),
                "activeOrganisms": len(self.organisms),
                "activeColonies": len(self.colonies),
                "activeSynapsesProxy": max(0, sum(max(0, len(org.cells) - 1) for org in self.organisms.values())),
                "memoryBytesProxy": len(self.cells) * self.vector_size * 8 + len(self.organisms) * 192 + len(self.colonies) * 144,
                "resourceScore": round(sum(org.utility for org in self.organisms.values()), 4),
                "events": len(self.events),
            },
            "cells": [asdict(cell) for cell in self.cells.values()],
            "organisms": organisms,
            "colonies": [asdict(colony) for colony in self.colonies.values()],
            "events": list(reversed(self.events[-12:])),
        }

    def state(self) -> dict[str, Any]:
        return self._state_payload()

    def state_hash(self) -> str:
        compact = json.dumps({
            "seed": self.seed,
            "step": self.step_count,
            "cells": [asdict(cell) for cell in self.cells.values()],
            "organisms": [asdict(organism) for organism in self.organisms.values()],
            "colonies": [asdict(colony) for colony in self.colonies.values()],
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(compact.encode()).hexdigest()[:12]

    def evaluate_hidden(self) -> dict[str, Any]:
        before = self.state_hash()
        evaluator_rng = random.Random(f"{self.seed}:hidden-evaluation")
        assignments: list[tuple[str, str]] = []
        for label in SHAPES:
            for offset in range(8):
                vector = self._vector_for(label, offset * 0.32, 0.025, 0.0, evaluator_rng)
                if not self.organisms:
                    assigned = "unassigned"
                else:
                    assigned = min(
                        self.organisms.values(),
                        key=lambda org: self._distance(vector, org.specialization),
                    ).id
                assignments.append((label, assigned))
        by_organism: dict[str, list[str]] = {}
        for label, organism_id in assignments:
            by_organism.setdefault(organism_id, []).append(label)
        correct = sum(max(labels.count(label) for label in set(labels)) for labels in by_organism.values())
        purity = correct / max(1, len(assignments))
        after = self.state_hash()
        return {
            "modelModified": before != after,
            "sampleCount": len(assignments),
            "purity": round(purity, 3),
            "communities": [
                {"organismId": organism_id, "dominantHiddenLabel": max(set(labels), key=labels.count), "samples": len(labels)}
                for organism_id, labels in by_organism.items()
            ],
            "note": "Hidden labels were used only by this read-only evaluator.",
        }

    def ablate(self, organism_id: str) -> dict[str, Any]:
        if organism_id not in self.organisms:
            raise KeyError(organism_id)
        before = self.state_hash()
        evaluator_rng = random.Random(f"{self.seed}:ablation:{organism_id}")
        vectors = [
            self._vector_for(shape, index * 0.27, 0.03, 0.0, evaluator_rng)
            for index, shape in enumerate(SHAPES * 4)
        ]

        def mean_error(excluded: str | None) -> float:
            candidates = [org for org in self.organisms.values() if org.id != excluded]
            if not candidates:
                return 1.0
            errors = []
            for vector in vectors:
                errors.append(min(self._distance(vector, org.specialization) for org in candidates))
            return float(np.mean(errors))

        with_component = mean_error(None)
        without_component = mean_error(organism_id)
        after = self.state_hash()
        return {
            "organismId": organism_id,
            "modelModified": before != after,
            "baselineLoss": round(with_component, 5),
            "ablatedLoss": round(without_component, 5),
            "delta": round(without_component - with_component, 5),
            "note": "Read-only deterministic ablation; the live ecosystem was not changed.",
        }

    def report(self) -> dict[str, Any]:
        return {
            "schema": "colonymind.report.v1",
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "simulation": {"seed": self.seed, "stepCount": self.step_count, "stateHash": self.state_hash(), "labelsUsedForTraining": False},
            "state": self.state(),
            "limitations": [
                "The resource score is a compute proxy, not measured physical energy in watts.",
                "Basic shapes are a controlled initial benchmark, not a camera-vision result.",
                "The current hidden evaluation reports purity only; standard NMI and ARI are planned for the benchmark phase.",
            ],
        }
