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
    x: float = 50.0
    y: float = 50.0
    heading: float = 0.0
    distance_travelled: float = 0.0


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

    retina_side = 16
    vector_size = retina_side * retina_side

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
        self.information_patches: list[dict[str, Any]] = []
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

    @staticmethod
    def _inside_shape(shape: str, x: float, y: float) -> bool:
        if shape == "circle":
            return x * x + y * y <= 0.86
        if shape == "square":
            return max(abs(x), abs(y)) <= 0.82
        if shape == "triangle":
            return -0.92 <= y <= 0.78 and abs(x) <= 0.92 * (y + 0.92) / 1.70
        raise ValueError(f"Unknown visual generator shape: {shape}")

    def _retina_for(
        self,
        shape: str,
        rotation: float,
        scale: float,
        noise: float,
        occlusion: float,
        offset_x: float,
        offset_y: float,
        rng: random.Random | None = None,
    ) -> np.ndarray:
        source_rng = rng or self.rng
        cosine = math.cos(rotation)
        sine = math.sin(rotation)
        pixels = np.zeros((self.retina_side, self.retina_side), dtype=np.float64)

        for row in range(self.retina_side):
            for column in range(self.retina_side):
                retinal_x = ((column + 0.5) / self.retina_side) * 2.0 - 1.0 - offset_x
                retinal_y = ((row + 0.5) / self.retina_side) * 2.0 - 1.0 - offset_y
                local_x = (cosine * retinal_x + sine * retinal_y) / scale
                local_y = (-sine * retinal_x + cosine * retinal_y) / scale
                signal = 0.94 if self._inside_shape(shape, local_x, local_y) else 0.025
                pixels[row, column] = signal + source_rng.uniform(-noise, noise)

        if occlusion > 0:
            span = max(1, min(self.retina_side - 1, round(self.retina_side * math.sqrt(occlusion))))
            start_row = source_rng.randrange(0, self.retina_side - span + 1)
            start_column = source_rng.randrange(0, self.retina_side - span + 1)
            pixels[start_row : start_row + span, start_column : start_column + span] *= 0.10

        return np.clip(pixels.reshape(self.vector_size), 0.0, 1.0)

    def _sample(self) -> tuple[np.ndarray, dict[str, Any], str]:
        shape = self.rng.choice(SHAPES)
        rotation = self.rng.uniform(-math.pi, math.pi)
        scale = self.rng.uniform(0.38, 0.82)
        noise = self.rng.uniform(0.008, 0.14)
        occlusion = self.rng.choice((0.0, 0.0, 0.10, 0.18, 0.25))
        offset_limit = max(0.04, (1.0 - scale) * 0.34)
        offset_x = self.rng.uniform(-offset_limit, offset_limit)
        offset_y = self.rng.uniform(-offset_limit, offset_limit)
        vector = self._retina_for(shape, rotation, scale, noise, occlusion, offset_x, offset_y)
        sample_id = self._next_id("sample")
        public = {
            "id": sample_id,
            "rotation": round(rotation, 3),
            "scale": round(scale, 3),
            "noise": round(noise, 3),
            "occlusion": occlusion,
            "offsetX": round(offset_x, 3),
            "offsetY": round(offset_y, 3),
            "retinaSide": self.retina_side,
            "retinaPixels": vector.round(3).tolist(),
        }
        # The private generator label is returned separately and never passed to learning or public state.
        return vector, public, shape

    def _create_organism(self, prototype: np.ndarray, reason: str, parent: Organism | None = None) -> Organism:
        organism_id = self._next_id("organism")
        information_x, information_y = self._information_coordinates(prototype)
        organism = Organism(
            id=organism_id,
            lineage=parent.lineage if parent else organism_id,
            color=COLORS[(self._ids["organism"] - 1) % len(COLORS)],
            specialization=prototype.round(4).tolist(),
            energy=0.54 if parent else 0.62,
            x=min(92.0, max(8.0, information_x + self.rng.uniform(-6.0, 6.0))),
            y=min(92.0, max(8.0, information_y + self.rng.uniform(-6.0, 6.0))),
            heading=self.rng.uniform(-math.pi, math.pi),
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

    def _information_coordinates(self, vector: np.ndarray) -> tuple[float, float]:
        """Project retinal input into a deterministic 2-D information habitat."""
        centered = vector - float(np.mean(vector))
        indices = np.arange(self.vector_size, dtype=np.float64) + 1.0
        norm = float(np.sum(np.abs(centered))) or 1.0
        projection_x = float(np.sum(centered * np.sin(indices * 0.731)) / norm)
        projection_y = float(np.sum(centered * np.cos(indices * 1.173)) / norm)
        x = 50.0 + math.tanh(projection_x * 4.8) * 38.0
        y = 50.0 + math.tanh(projection_y * 4.8) * 34.0
        return x, y

    def _record_information_patch(self, vector: np.ndarray, sample_id: str, novelty: float) -> dict[str, Any]:
        x, y = self._information_coordinates(vector)
        patch = {
            "id": sample_id,
            "x": round(x, 3),
            "y": round(y, 3),
            "amount": round(min(1.0, 0.28 + novelty * 4.5), 3),
            "novelty": round(novelty, 4),
            "createdStep": self.step_count,
            "consumedBy": None,
        }
        self.information_patches.append(patch)
        self.information_patches = self.information_patches[-18:]
        return patch

    def _move_organisms(
        self,
        responses: list[tuple[Organism, float, np.ndarray]],
        patch: dict[str, Any],
        winner_id: str,
    ) -> None:
        colony_centers: dict[str, tuple[float, float]] = {}
        for colony in self.colonies.values():
            members = [self.organisms[member_id] for member_id in colony.member_ids if member_id in self.organisms]
            if members:
                colony_centers[colony.id] = (
                    sum(member.x for member in members) / len(members),
                    sum(member.y for member in members) / len(members),
                )

        for index, (organism, activation, _reconstruction) in enumerate(responses):
            target_x = float(patch["x"])
            target_y = float(patch["y"])
            if organism.colony_id in colony_centers and organism.id != winner_id:
                center_x, center_y = colony_centers[organism.colony_id]
                target_x = target_x * 0.58 + center_x * 0.42
                target_y = target_y * 0.58 + center_y * 0.42
            desired = math.atan2(target_y - organism.y, target_x - organism.x)
            steering = 0.16 + min(0.20, activation * 0.18)
            organism.heading += math.atan2(
                math.sin(desired - organism.heading),
                math.cos(desired - organism.heading),
            ) * steering
            organism.heading += math.sin(self.step_count * 0.17 + index * 2.3) * (0.09 if activation < 0.35 else 0.025)
            travel = (0.22 + activation * 0.68) * (0.55 + min(1.0, organism.energy) * 0.45)
            previous_x, previous_y = organism.x, organism.y
            organism.x = min(94.0, max(6.0, organism.x + math.cos(organism.heading) * travel))
            organism.y = min(94.0, max(6.0, organism.y + math.sin(organism.heading) * travel))
            organism.distance_travelled += math.hypot(organism.x - previous_x, organism.y - previous_y)

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
            if organism.age_steps > 300 and organism.utility < -0.018 and len(self.organisms) > 1:
                colony_id = organism.colony_id
                for cell_id in organism.cells:
                    self.cells.pop(cell_id, None)
                self.organisms.pop(organism.id, None)
                if colony_id and colony_id in self.colonies:
                    colony = self.colonies[colony_id]
                    colony.member_ids = [member_id for member_id in colony.member_ids if member_id != organism.id]
                    colony.core_members = [member_id for member_id in colony.core_members if member_id != organism.id]
                    if len(colony.member_ids) < 2:
                        for member_id in colony.member_ids:
                            if member_id in self.organisms:
                                self.organisms[member_id].colony_id = None
                        self.colonies.pop(colony_id, None)
                        self._event("COLONY_DISSOLVED", colony_id, ["INSUFFICIENT_ACTIVE_MEMBERS"], {"remainingMembers": len(colony.member_ids)})
                self._event("ORGANISM_ARCHIVED", organism.id, ["PERSISTENT_NEGATIVE_MARGINAL_VALUE"], {"utility": organism.utility})
                break

    def step(self, count: int = 1) -> dict[str, Any]:
        for _ in range(max(1, min(count, 240))):
            self.step_count += 1
            vector, public, _label = self._sample()
            self.current_stimulus = public
            novelty = min(
                (self._distance(vector, organism.specialization) for organism in self.organisms.values()),
                default=1.0,
            )
            information_patch = self._record_information_patch(vector, public["id"], novelty)
            if not self.organisms:
                pioneer = self._create_organism(vector, "FIRST_UNLABELED_STIMULUS")
                information_patch["consumedBy"] = pioneer.id
                information_patch["amount"] = 0.12
                self.loss_history.append(0.0)
                continue
            responses = [(org, *self._organism_response(org, vector)[:2]) for org in self.organisms.values()]
            responses.sort(key=lambda row: row[1], reverse=True)
            winner, winner_activation, reconstruction = responses[0]
            self._move_organisms(responses, information_patch, winner.id)
            information_patch["consumedBy"] = winner.id
            information_patch["amount"] = round(
                max(0.06, information_patch["amount"] * (1.0 - winner_activation * 0.72)),
                3,
            )
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
        for organism in self.organisms.values():
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
                "x": round(organism.x, 2),
                "y": round(organism.y, 2),
                "heading": round(organism.heading, 3),
                "distanceTravelled": round(organism.distance_travelled, 2),
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
            "informationPatches": self.information_patches,
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
                scale = 0.42 + (offset % 4) * 0.11
                shift = ((offset % 3) - 1) * 0.07
                vector = self._retina_for(
                    label,
                    offset * 0.39,
                    scale,
                    0.035,
                    0.10 if offset % 4 == 0 else 0.0,
                    shift,
                    -shift,
                    evaluator_rng,
                )
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
            self._retina_for(
                shape,
                index * 0.31,
                0.45 + (index % 3) * 0.12,
                0.035,
                0.0,
                ((index % 3) - 1) * 0.06,
                0.0,
                evaluator_rng,
            )
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
