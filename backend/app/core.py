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
    born_step: int = 0
    wins: int = 0
    last_active_step: int = 0
    lifecycle_state: str = "young"
    protected_until: int = 0
    low_value_steps: int = 0
    dormant_since: int | None = None
    reactivations: int = 0
    last_reactivated_step: int | None = None
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

    retina_side = 64
    vector_size = retina_side * retina_side
    maturity_age = 120
    maturity_wins = 8
    minimum_lifespan = 5_000
    dormancy_after_inactive = 2_000
    archive_after_inactive = 5_000
    low_value_grace = 2_000
    reactivation_distance = 0.035
    redundancy_distance = 0.018
    archive_ablation_tolerance = 0.0005
    max_processing_organisms = 8
    max_resident_organisms = 16
    response_committee_size = 4
    replay_capacity = 64

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
        self.structural_history: list[dict[str, Any]] = []
        self.event_totals: dict[str, int] = {}
        self.audit_history: list[dict[str, Any]] = []
        self.replay_buffer: list[np.ndarray] = []
        self.organism_archive: list[dict[str, Any]] = []
        self.current_committee_ids: list[str] = []
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
        event = {
            "step": self.step_count,
            "kind": kind,
            "entityId": entity_id,
            "reasons": reasons,
            "metrics": {key: round(value, 5) for key, value in metrics.items()},
        }
        self.events.append(event)
        self.events = self.events[-24:]
        self.event_totals[kind] = self.event_totals.get(kind, 0) + 1
        if kind != "SESSION_STARTED":
            self.structural_history.append(event)
            self.structural_history = self.structural_history[-256:]

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
        render_mode: str = "filled",
    ) -> np.ndarray:
        if render_mode not in {"filled", "outline"}:
            raise ValueError(f"Unknown retinal render mode: {render_mode}")
        source_rng = rng or self.rng
        cosine = math.cos(rotation)
        sine = math.sin(rotation)
        coverage = np.zeros((self.retina_side, self.retina_side), dtype=np.float64)
        subpixel_offsets = (-0.25, 0.25)

        columns, rows = np.meshgrid(
            np.arange(self.retina_side, dtype=np.float64),
            np.arange(self.retina_side, dtype=np.float64),
        )

        def inside(local_x: np.ndarray, local_y: np.ndarray) -> np.ndarray:
            if shape == "circle":
                return local_x * local_x + local_y * local_y <= 0.86
            if shape == "square":
                return np.maximum(np.abs(local_x), np.abs(local_y)) <= 0.82
            if shape == "triangle":
                return (-0.92 <= local_y) & (local_y <= 0.78) & (np.abs(local_x) <= 0.92 * (local_y + 0.92) / 1.70)
            raise ValueError(f"Unknown visual generator shape: {shape}")

        for subpixel_y in subpixel_offsets:
            for subpixel_x in subpixel_offsets:
                retinal_x = ((columns + 0.5 + subpixel_x) / self.retina_side) * 2.0 - 1.0 - offset_x
                retinal_y = ((rows + 0.5 + subpixel_y) / self.retina_side) * 2.0 - 1.0 - offset_y
                local_x = (cosine * retinal_x + sine * retinal_y) / scale
                local_y = (-sine * retinal_x + cosine * retinal_y) / scale
                outer = inside(local_x, local_y)
                if render_mode == "outline":
                    # A geometrically inset copy produces a scale-consistent contour.
                    # The learner is still given pixels only; this mode is public metadata,
                    # not a semantic shape label.
                    coverage += outer & ~inside(local_x / 0.84, local_y / 0.84)
                else:
                    coverage += outer

        signal = 0.025 + (coverage / 4.0) * 0.915
        noise_values = (
            np.fromiter(
                (source_rng.uniform(-noise, noise) for _ in range(self.vector_size)),
                dtype=np.float64,
                count=self.vector_size,
            ).reshape((self.retina_side, self.retina_side))
            if noise > 0.0
            else np.zeros((self.retina_side, self.retina_side), dtype=np.float64)
        )
        pixels = signal + noise_values

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
        render_mode = self.rng.choice(("filled", "outline"))
        vector = self._retina_for(
            shape,
            rotation,
            scale,
            noise,
            occlusion,
            offset_x,
            offset_y,
            render_mode=render_mode,
        )
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
            "renderMode": render_mode,
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
            born_step=self.step_count,
            last_active_step=self.step_count,
            protected_until=self.step_count + self.minimum_lifespan,
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
        wave_x = np.sin(indices * 0.731)
        wave_y = np.cos(indices * 1.173)
        signal_energy = float(np.linalg.norm(centered)) or 1.0
        projection_x = float(np.dot(centered, wave_x) / (signal_energy * float(np.linalg.norm(wave_x))))
        projection_y = float(np.dot(centered, wave_y) / (signal_energy * float(np.linalg.norm(wave_y))))
        x = 50.0 + math.tanh(projection_x * 18.0) * 42.0
        y = 50.0 + math.tanh(projection_y * 18.0) * 38.0
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
                target_x = target_x * 0.82 + center_x * 0.18
                target_y = target_y * 0.82 + center_y * 0.18

            # Local exclusion keeps independently useful organisms legible instead
            # of collapsing into one decorative blob. Colonies provide cohesion,
            # while this short-range force preserves distinct members.
            for other_index, other in enumerate(self.organisms.values()):
                if other.id == organism.id:
                    continue
                difference_x = organism.x - other.x
                difference_y = organism.y - other.y
                distance = math.hypot(difference_x, difference_y)
                if distance < 0.001:
                    angle = (index + other_index + 1) * 2.399
                    difference_x, difference_y, distance = math.cos(angle), math.sin(angle), 1.0
                if distance < 9.0:
                    strength = (9.0 - distance) / 9.0
                    target_x += difference_x / distance * strength * 18.0
                    target_y += difference_y / distance * strength * 18.0
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

        # Resolve the remaining overlap after movement. Two small deterministic
        # relaxation passes keep bodies selectable without freezing their motion.
        organisms = list(self.organisms.values())
        for _pass in range(2):
            for first_index, first in enumerate(organisms):
                for second_index, second in enumerate(organisms[first_index + 1 :], first_index + 1):
                    difference_x = first.x - second.x
                    difference_y = first.y - second.y
                    distance = math.hypot(difference_x, difference_y)
                    if distance < 0.001:
                        angle = (first_index + second_index + 1) * 2.399
                        difference_x, difference_y, distance = math.cos(angle), math.sin(angle), 1.0
                    if distance >= 7.2:
                        continue
                    correction = (7.2 - distance) * 0.5
                    direction_x, direction_y = difference_x / distance, difference_y / distance
                    first.x = min(94.0, max(6.0, first.x + direction_x * correction))
                    first.y = min(94.0, max(6.0, first.y + direction_y * correction))
                    second.x = min(94.0, max(6.0, second.x - direction_x * correction))
                    second.y = min(94.0, max(6.0, second.y - direction_y * correction))

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

    def _processing_organisms(self) -> list[Organism]:
        return [organism for organism in self.organisms.values() if organism.lifecycle_state != "dormant"]

    def _active_committee(self) -> list[Organism]:
        return [
            self.organisms[organism_id]
            for organism_id in self.current_committee_ids
            if organism_id in self.organisms
            and self.organisms[organism_id].lifecycle_state != "dormant"
        ]

    def _advance_lifecycle(self, vector: np.ndarray) -> None:
        for organism in self.organisms.values():
            organism.age_steps += 1
            if organism.last_active_step < self.step_count:
                organism.contribution *= 0.998
            if organism.utility < -0.012 and organism.contribution < 0.001:
                organism.low_value_steps += 1
            else:
                organism.low_value_steps = max(0, organism.low_value_steps - 4)

            if (
                organism.lifecycle_state == "young"
                and organism.age_steps >= self.maturity_age
                and organism.wins >= self.maturity_wins
            ):
                organism.lifecycle_state = "mature"
                self._event(
                    "ORGANISM_MATURED",
                    organism.id,
                    ["LONG_TERM_SPECIALIZATION_SURVIVED"],
                    {"age": organism.age_steps, "wins": organism.wins},
                )

            inactive_steps = self.step_count - organism.last_active_step
            may_sleep = organism.lifecycle_state == "mature" or organism.age_steps >= self.minimum_lifespan
            if (
                organism.lifecycle_state != "dormant"
                and may_sleep
                and inactive_steps >= self.dormancy_after_inactive
            ):
                organism.lifecycle_state = "dormant"
                organism.dormant_since = self.step_count
                self._event(
                    "ORGANISM_DORMANT",
                    organism.id,
                    ["LONG_TERM_INACTIVITY", "MEMORY_RETAINED_AT_LOW_COMPUTE"],
                    {"inactiveSteps": inactive_steps, "age": organism.age_steps},
                )

        dormant = [organism for organism in self.organisms.values() if organism.lifecycle_state == "dormant"]
        if not dormant:
            return
        closest, distance = min(
            ((organism, self._distance(vector, organism.specialization)) for organism in dormant),
            key=lambda item: item[1],
        )
        if distance <= self.reactivation_distance or not self._processing_organisms():
            closest.lifecycle_state = "mature"
            closest.dormant_since = None
            closest.reactivations += 1
            closest.last_reactivated_step = self.step_count
            closest.last_active_step = self.step_count
            self._event(
                "ORGANISM_REACTIVATED",
                closest.id,
                ["FAMILIAR_INFORMATION_RETURNED"],
                {"distance": distance, "reactivations": closest.reactivations},
            )

    def _replay_ablation_delta(self, organism_id: str) -> float:
        if not self.replay_buffer or organism_id not in self.organisms:
            return 1.0
        residents = list(self.organisms.values())
        alternatives = [organism for organism in residents if organism.id != organism_id]
        if not alternatives:
            return 1.0
        with_errors: list[float] = []
        without_errors: list[float] = []
        for vector in self.replay_buffer:
            with_errors.append(min(self._distance(vector, organism.specialization) for organism in residents))
            without_errors.append(min(self._distance(vector, organism.specialization) for organism in alternatives))
        return float(np.mean(without_errors) - np.mean(with_errors))

    def _update_cell_redundancy(self) -> None:
        """Estimate whether each cell is duplicating another cell in its organism."""
        for organism in self.organisms.values():
            resident_cells = [self.cells[cell_id] for cell_id in organism.cells if cell_id in self.cells]
            for cell in resident_cells:
                alternatives = [other for other in resident_cells if other.id != cell.id]
                if not alternatives:
                    cell.redundancy = 0.0
                    continue
                nearest = min(
                    self._distance(np.asarray(cell.prototype), other.prototype)
                    for other in alternatives
                )
                cell.redundancy = math.exp(-nearest / 0.012)

    def _archive_if_safe(self) -> None:
        if len(self.organisms) <= 1:
            return
        for organism in list(self.organisms.values()):
            inactive_steps = self.step_count - organism.last_active_step
            if (
                organism.lifecycle_state != "dormant"
                or self.step_count < organism.protected_until
                or organism.age_steps < self.minimum_lifespan
                or inactive_steps < self.archive_after_inactive
                or organism.low_value_steps < self.low_value_grace
            ):
                continue
            others = [other for other in self.organisms.values() if other.id != organism.id]
            nearest_distance = min(
                (self._distance(np.asarray(organism.specialization), other.specialization) for other in others),
                default=1.0,
            )
            if nearest_distance > self.redundancy_distance:
                continue
            ablation_delta = self._replay_ablation_delta(organism.id)
            if ablation_delta > self.archive_ablation_tolerance:
                continue

            colony_id = organism.colony_id
            archived_cells = len(organism.cells)
            self.organism_archive.append({
                "id": organism.id,
                "lineage": organism.lineage,
                "bornStep": organism.born_step,
                "archivedStep": self.step_count,
                "ageSteps": organism.age_steps,
                "wins": organism.wins,
                "reactivations": organism.reactivations,
                "cells": archived_cells,
                "nearestDistance": round(nearest_distance, 6),
                "replayAblationDelta": round(ablation_delta, 6),
                "reason": "REDUNDANT_LONG_DORMANT_MEMORY",
            })
            self.organism_archive = self.organism_archive[-100:]
            for cell_id in organism.cells:
                self.cells.pop(cell_id, None)
            self.organisms.pop(organism.id, None)
            self._event(
                "CELLS_ARCHIVED",
                organism.id,
                ["PARENT_MEMORY_SAFELY_ARCHIVED"],
                {"cells": archived_cells},
            )
            if colony_id and colony_id in self.colonies:
                colony = self.colonies[colony_id]
                colony.member_ids = [member_id for member_id in colony.member_ids if member_id != organism.id]
                colony.core_members = [member_id for member_id in colony.core_members if member_id != organism.id]
                if len(colony.member_ids) < 2:
                    for member_id in colony.member_ids:
                        if member_id in self.organisms:
                            self.organisms[member_id].colony_id = None
                    self.colonies.pop(colony_id, None)
                    self._event(
                        "COLONY_DISSOLVED",
                        colony_id,
                        ["INSUFFICIENT_ACTIVE_MEMBERS"],
                        {"remainingMembers": len(colony.member_ids)},
                    )
            self._event(
                "ORGANISM_ARCHIVED",
                organism.id,
                ["LONG_DORMANCY", "REDUNDANT_MEMORY", "NON_POSITIVE_REPLAY_ABLATION"],
                {
                    "utility": organism.utility,
                    "inactiveSteps": inactive_steps,
                    "nearestDistance": nearest_distance,
                    "replayAblationDelta": ablation_delta,
                },
            )
            break

    def _create_colony_if_useful(self) -> None:
        unassigned = [
            organism
            for organism in self._processing_organisms()
            if organism.colony_id is None and organism.lifecycle_state == "mature"
        ]
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
        processing = self._processing_organisms()
        best = max(processing, key=lambda org: org.utility, default=None)
        novelty = min(
            (self._distance(vector, organism.specialization) for organism in self.organisms.values()),
            default=1.0,
        )
        if loss > 0.052:
            self.high_residual_streak += 1
        else:
            self.high_residual_streak = max(0, self.high_residual_streak - 1)
        novel_regime = novelty > 0.045 and len(processing) < 3 and self.step_count >= 24
        capacity_available = (
            len(processing) < self.max_processing_organisms
            and len(self.organisms) < self.max_resident_organisms
        )
        if (self.high_residual_streak >= 3 or novel_regime) and capacity_available:
            reason = "NOVEL_UNLABELED_VISUAL_REGIME" if novel_regime else "PERSISTENT_UNSERVED_VISUAL_RESIDUAL"
            self._create_organism(vector, reason, best)
            self.high_residual_streak = 0
        else:
            if best and loss > 0.025 and len(best.cells) < 8:
                self._create_cell(best, vector, "LOCAL_RESIDUAL_SPECIALIZATION")
        self._update_cell_redundancy()
        self._create_colony_if_useful()
        self._archive_if_safe()

    def step(self, count: int = 1) -> dict[str, Any]:
        for _ in range(max(1, min(count, 240))):
            self.step_count += 1
            vector, public, _label = self._sample()
            self.current_stimulus = public
            self.replay_buffer.append(vector.copy())
            self.replay_buffer = self.replay_buffer[-self.replay_capacity :]
            self._advance_lifecycle(vector)
            novelty = min(
                (self._distance(vector, organism.specialization) for organism in self.organisms.values()),
                default=1.0,
            )
            information_patch = self._record_information_patch(vector, public["id"], novelty)
            if not self.organisms:
                pioneer = self._create_organism(vector, "FIRST_UNLABELED_STIMULUS")
                self.current_committee_ids = [pioneer.id]
                information_patch["consumedBy"] = pioneer.id
                information_patch["amount"] = 0.12
                self.loss_history.append(0.0)
                continue
            available = self._processing_organisms()
            processing = sorted(
                available,
                key=lambda organism: self._distance(vector, organism.specialization),
            )[: self.response_committee_size]
            self.current_committee_ids = [organism.id for organism in processing]
            responses = [(org, *self._organism_response(org, vector)[:2]) for org in processing]
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
            processing_cells = sum(len(organism.cells) for organism in processing)
            active_cost = 0.0018 * len(winner.cells) + 0.0008 * processing_cells
            communication_cost = 0.003 if winner.colony_id else 0.0
            winner.contribution = max(0.0, improvement + 0.12 * error)
            winner.utility = 0.84 * winner.utility + 0.16 * (winner.contribution - active_cost - communication_cost)
            winner.energy = min(1.5, max(0.0, winner.energy + winner.utility * 0.11))
            winner.wins += 1
            winner.last_active_step = self.step_count
            recently_reactivated = (
                winner.last_reactivated_step is not None
                and self.step_count - winner.last_reactivated_step <= 500
            )
            plasticity = 1.0 if winner.lifecycle_state == "young" else (0.55 if recently_reactivated else 0.35)
            for cell_id in winner.cells:
                cell = self.cells[cell_id]
                activation = math.exp(-self._distance(vector, cell.prototype) / 0.06)
                cell.activation = activation
                cell.age_steps += 1
                learning_rate = (0.018 + 0.055 * activation) * plasticity
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
        processing = self._active_committee()
        dormant = [organism for organism in self.organisms.values() if organism.lifecycle_state == "dormant"]
        processing_ids = {organism.id for organism in processing}
        processing_cells = [cell for cell in self.cells.values() if cell.organism_id in processing_ids]
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
                "bornStep": organism.born_step,
                "wins": organism.wins,
                "lastActiveStep": organism.last_active_step,
                "inactiveSteps": max(0, self.step_count - organism.last_active_step),
                "lifecycleState": organism.lifecycle_state,
                "protectedUntil": organism.protected_until,
                "lowValueSteps": organism.low_value_steps,
                "dormantSince": organism.dormant_since,
                "reactivations": organism.reactivations,
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
                "activeCells": len(processing_cells),
                "residentCells": len(self.cells),
                "activeOrganisms": len(processing),
                "residentOrganisms": len(self.organisms),
                "dormantOrganisms": len(dormant),
                "activeColonies": len(self.colonies),
                "activeSynapsesProxy": max(0, sum(max(0, len(org.cells) - 1) for org in processing)),
                "memoryBytesProxy": len(self.cells) * self.vector_size * 8 + len(self.organisms) * 192 + len(self.colonies) * 144,
                "resourceScore": round(
                    sum(org.utility for org in processing)
                    - 0.00005 * sum(len(org.cells) for org in dormant),
                    4,
                ),
                "events": len(self.events),
            },
            "cells": [
                {
                    "id": cell.id,
                    "organism_id": cell.organism_id,
                    "energy": round(cell.energy, 4),
                    "utility": round(cell.utility, 5),
                    "activation": round(cell.activation, 5),
                    "age_steps": cell.age_steps,
                    "redundancy": round(cell.redundancy, 5),
                }
                for cell in self.cells.values()
            ],
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
                    "outline" if offset % 2 else "filled",
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

    @staticmethod
    def _dilate_mask(mask: np.ndarray, radius: int = 2) -> np.ndarray:
        padded = np.pad(mask, radius, mode="constant", constant_values=False)
        expanded = np.zeros_like(mask, dtype=bool)
        height, width = mask.shape
        for offset_y in range(radius * 2 + 1):
            for offset_x in range(radius * 2 + 1):
                expanded |= padded[offset_y : offset_y + height, offset_x : offset_x + width]
        return expanded

    def _normalize_drawing(self, pixels: list[float]) -> np.ndarray:
        image = np.clip(np.asarray(pixels, dtype=np.float64), 0.0, 1.0).reshape(
            (self.retina_side, self.retina_side)
        )
        active = image > 0.08
        if int(np.sum(active)) < 12:
            raise ValueError("Draw a complete shape before asking the auditor.")

        rows, columns = np.where(active)
        crop = image[rows.min() : rows.max() + 1, columns.min() : columns.max() + 1]
        crop_height, crop_width = crop.shape
        target_extent = 44
        scale = min(target_extent / crop_height, target_extent / crop_width)
        resized_height = max(1, round(crop_height * scale))
        resized_width = max(1, round(crop_width * scale))
        source_rows = np.clip(
            np.round(np.linspace(0, crop_height - 1, resized_height)).astype(int),
            0,
            crop_height - 1,
        )
        source_columns = np.clip(
            np.round(np.linspace(0, crop_width - 1, resized_width)).astype(int),
            0,
            crop_width - 1,
        )
        resized = crop[np.ix_(source_rows, source_columns)]
        normalized = np.zeros((self.retina_side, self.retina_side), dtype=np.float64)
        start_row = (self.retina_side - resized_height) // 2
        start_column = (self.retina_side - resized_width) // 2
        normalized[
            start_row : start_row + resized_height,
            start_column : start_column + resized_width,
        ] = resized
        return np.clip(0.025 + normalized.reshape(self.vector_size) * 0.915, 0.0, 1.0)

    def _audit_drawing_geometry(self, vector: np.ndarray) -> tuple[str, float, float, dict[str, float]]:
        drawing_mask = vector.reshape((self.retina_side, self.retina_side)) > 0.24
        drawing_tolerance = self._dilate_mask(drawing_mask)
        rotations = {
            "circle": (0.0,),
            "square": tuple(index * (math.pi / 2.0) / 12.0 for index in range(12)),
            "triangle": tuple(index * (math.pi * 2.0) / 24.0 for index in range(24)),
        }
        scores: dict[str, float] = {}
        for shape in SHAPES:
            best_score = 0.0
            for scale in (0.74, 0.82):
                for rotation in rotations[shape]:
                    template = self._retina_for(
                        shape,
                        rotation,
                        scale,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        random.Random(0),
                        "outline",
                    ).reshape((self.retina_side, self.retina_side)) > 0.24
                    template_tolerance = self._dilate_mask(template)
                    drawn_near_template = float(np.mean(template_tolerance[drawing_mask]))
                    template_near_drawing = float(np.mean(drawing_tolerance[template]))
                    score = math.sqrt(max(0.0, drawn_near_template * template_near_drawing))
                    best_score = max(best_score, score)
            scores[shape] = best_score

        label = max(scores, key=scores.get)
        peak = scores[label]
        weights = {shape: math.exp((score - peak) * 9.0) for shape, score in scores.items()}
        confidence = weights[label] / sum(weights.values())
        return label, confidence, peak, scores

    def audit_drawing(self, pixels: list[float]) -> dict[str, Any]:
        """Read-only learner probe plus an explicitly external geometric auditor."""
        before = self.state_hash()
        vector = self._normalize_drawing(pixels)
        auditor_label, auditor_confidence, geometric_match, label_scores = self._audit_drawing_geometry(vector)

        selected: Organism | None = None
        learner_confidence = 0.0
        reconstruction_error: float | None = None
        if self.organisms:
            distances = [(organism, self._distance(vector, organism.specialization)) for organism in self.organisms.values()]
            distances.sort(key=lambda item: item[1])
            selected, reconstruction_error = distances[0]
            proximity = [math.exp(-distance / 0.06) for _organism, distance in distances]
            learner_confidence = proximity[0] / max(1e-12, sum(proximity))

        evaluation = self.evaluate_hidden()
        community = next(
            (
                item
                for item in evaluation["communities"]
                if selected is not None and item["organismId"] == selected.id
            ),
            None,
        )
        associated_label = community["dominantHiddenLabel"] if community else "unmapped"
        after = self.state_hash()
        result = {
            "modelModified": before != after,
            "stateHashBefore": before,
            "stateHashAfter": after,
            "retinaSide": self.retina_side,
            "normalizedPixels": vector.round(3).tolist(),
            "ecosystemResponse": {
                "organismId": selected.id if selected else None,
                "colonyId": selected.colony_id if selected else None,
                "confidence": round(learner_confidence, 3),
                "reconstructionError": round(reconstruction_error, 5) if reconstruction_error is not None else None,
            },
            "externalAuditor": {
                "drawnLabel": auditor_label,
                "confidence": round(auditor_confidence, 3),
                "geometricMatch": round(geometric_match, 3),
                "labelScores": {shape: round(score, 3) for shape, score in label_scores.items()},
                "organismAssociatedLabel": associated_label,
                "mappingSupport": community["samples"] if community else 0,
            },
            "agreement": selected is not None and associated_label == auditor_label,
            "note": "The geometric auditor owns all labels; the ecosystem and its live state remain unchanged.",
        }
        audit_id = f"audit-{len(self.audit_history) + 1:03d}"
        result["auditId"] = audit_id
        self.audit_history.append({
            "auditId": audit_id,
            "recordedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "step": self.step_count,
            "stateHash": after,
            "modelModified": result["modelModified"],
            "ecosystemResponse": result["ecosystemResponse"],
            "externalAuditor": result["externalAuditor"],
            "agreement": result["agreement"],
        })
        self.audit_history = self.audit_history[-100:]
        return result

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
                "outline" if index % 2 else "filled",
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
        state = self.state()
        loss_series = [round(value, 6) for value in self.loss_history]
        comparison_window = min(20, len(loss_series) // 2)
        loss_change = 0.0
        if comparison_window:
            loss_change = float(
                np.mean(loss_series[-comparison_window:])
                - np.mean(loss_series[:comparison_window])
            )

        resident_cells = list(self.cells.values())
        resident_organisms = list(self.organisms.values())
        processing_organisms = self._active_committee()
        processing_ids = {organism.id for organism in processing_organisms}
        active_cells = [cell for cell in resident_cells if cell.organism_id in processing_ids]
        dormant_organisms = [
            organism for organism in resident_organisms if organism.lifecycle_state == "dormant"
        ]
        active_colonies = list(self.colonies.values())
        cells_created = self.event_totals.get("CELL_BIRTH", 0)
        organisms_created = self.event_totals.get("ORGANISM_BIRTH", 0)
        organisms_archived = self.event_totals.get("ORGANISM_ARCHIVED", 0)
        colonies_formed = self.event_totals.get("COLONY_FORMED", 0)
        colonies_dissolved = self.event_totals.get("COLONY_DISSOLVED", 0)
        agreement_count = sum(int(audit["agreement"]) for audit in self.audit_history)
        agreement_rate = agreement_count / len(self.audit_history) if self.audit_history else None
        labels: dict[str, int] = {shape: 0 for shape in SHAPES}
        for audit in self.audit_history:
            label = audit["externalAuditor"]["drawnLabel"]
            labels[label] = labels.get(label, 0) + 1

        hidden_evaluation = self.evaluate_hidden() if resident_organisms else {
            "modelModified": False,
            "sampleCount": 0,
            "purity": 0.0,
            "communities": [],
            "note": "Train the ecosystem before running hidden evaluation.",
        }
        recommendations: list[dict[str, str]] = []
        if not self.audit_history:
            recommendations.append({
                "priority": "high",
                "evidence": "No Draw & Audit trials have been recorded.",
                "action": "Probe every shape at several rotations before comparing architectures.",
            })
        elif agreement_rate is not None and agreement_rate < 0.70:
            recommendations.append({
                "priority": "high",
                "evidence": f"Draw & Audit agreement is {agreement_rate:.1%}.",
                "action": "Increase training diversity and inspect which organism communities absorb conflicting shapes.",
            })
        if hidden_evaluation["purity"] < 0.75 and resident_organisms:
            recommendations.append({
                "priority": "high",
                "evidence": f"Hidden-label community purity is {hidden_evaluation['purity']:.1%}.",
                "action": "Tune novelty and structural-review thresholds to encourage cleaner specialization.",
            })
        if loss_change > 0.005:
            recommendations.append({
                "priority": "medium",
                "evidence": f"Recent loss increased by {loss_change:.5f} across comparison windows.",
                "action": "Reduce prototype learning rate or add a replay buffer for previously learned visual regimes.",
            })
        if processing_organisms and len(active_cells) / len(processing_organisms) >= 7.0:
            recommendations.append({
                "priority": "medium",
                "evidence": "Mean cells per organism is near the current capacity limit.",
                "action": "Compare cell splitting against organism birth using multi-seed resource-score ablations.",
            })
        if len(processing_organisms) >= 2 and not active_colonies:
            recommendations.append({
                "priority": "medium",
                "evidence": "Multiple organisms exist without a persistent colony.",
                "action": "Inspect diversity and synergy thresholds to determine whether cooperation is being undervalued.",
            })
        if dormant_organisms:
            recommendations.append({
                "priority": "low",
                "evidence": f"{len(dormant_organisms)} long-term memories are dormant and consume no learning updates.",
                "action": "Present related visual regimes to test similarity-triggered reactivation before considering archival.",
            })
        if not recommendations:
            recommendations.append({
                "priority": "low",
                "evidence": "No current heuristic warning crossed its threshold.",
                "action": "Repeat the benchmark across multiple seeds and compare report files before changing the architecture.",
            })

        return {
            "schema": "colonymind.performance-report.v3",
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "simulation": {
                "seed": self.seed,
                "stepCount": self.step_count,
                "stateHash": self.state_hash(),
                "retinaSide": self.retina_side,
                "labelsUsedForTraining": False,
            },
            "performance": {
                "learning": {
                    "currentLoss": state["metrics"]["loss"],
                    "meanRecentLoss": state["metrics"]["meanLoss"],
                    "lossWindowChange": round(loss_change, 6),
                    "recentLossSeries": loss_series,
                    "resourceScore": state["metrics"]["resourceScore"],
                    "activeSynapsesProxy": state["metrics"]["activeSynapsesProxy"],
                    "memoryBytesProxy": state["metrics"]["memoryBytesProxy"],
                },
                "cells": {
                    "active": len(active_cells),
                    "resident": len(resident_cells),
                    "created": cells_created,
                    "archivedWithOrganisms": max(0, cells_created - len(resident_cells)),
                    "meanEnergy": round(float(np.mean([cell.energy for cell in active_cells])), 5) if active_cells else 0.0,
                    "meanUtility": round(float(np.mean([cell.utility for cell in active_cells])), 6) if active_cells else 0.0,
                    "meanActivation": round(float(np.mean([cell.activation for cell in active_cells])), 6) if active_cells else 0.0,
                    "meanRedundancy": round(float(np.mean([cell.redundancy for cell in active_cells])), 6) if active_cells else 0.0,
                    "prototypeUpdateOperations": sum(cell.age_steps for cell in resident_cells),
                    "byOrganism": {organism.id: len(organism.cells) for organism in resident_organisms},
                },
                "population": {
                    "activeOrganisms": len(processing_organisms),
                    "residentOrganisms": len(resident_organisms),
                    "dormantOrganisms": len(dormant_organisms),
                    "youngOrganisms": sum(organism.lifecycle_state == "young" for organism in resident_organisms),
                    "matureOrganisms": sum(organism.lifecycle_state == "mature" for organism in resident_organisms),
                    "organismsCreated": organisms_created,
                    "organismsArchived": organisms_archived,
                    "meanEnergy": round(float(np.mean([organism.energy for organism in resident_organisms])), 5) if resident_organisms else 0.0,
                    "meanUtility": round(float(np.mean([organism.utility for organism in resident_organisms])), 6) if resident_organisms else 0.0,
                    "meanAgeSteps": round(float(np.mean([organism.age_steps for organism in resident_organisms])), 2) if resident_organisms else 0.0,
                    "meanWins": round(float(np.mean([organism.wins for organism in resident_organisms])), 2) if resident_organisms else 0.0,
                    "totalReactivations": sum(organism.reactivations for organism in resident_organisms),
                    "lineages": len({organism.lineage for organism in resident_organisms}),
                    "lifecyclePolicy": {
                        "maturityAge": self.maturity_age,
                        "maturityWins": self.maturity_wins,
                        "minimumLifespan": self.minimum_lifespan,
                        "dormancyAfterInactive": self.dormancy_after_inactive,
                        "archiveAfterInactive": self.archive_after_inactive,
                        "responseCommitteeSize": self.response_committee_size,
                        "replayCapacity": self.replay_capacity,
                    },
                    "residents": [
                        {
                            "id": organism.id,
                            "state": organism.lifecycle_state,
                            "ageSteps": organism.age_steps,
                            "wins": organism.wins,
                            "inactiveSteps": max(0, self.step_count - organism.last_active_step),
                            "protectedUntil": organism.protected_until,
                            "reactivations": organism.reactivations,
                        }
                        for organism in resident_organisms
                    ],
                    "archiveRegistry": self.organism_archive,
                },
                "colonies": {
                    "active": len(active_colonies),
                    "formed": colonies_formed,
                    "dissolved": colonies_dissolved,
                    "meanSynergy": round(float(np.mean([colony.synergy for colony in active_colonies])), 6) if active_colonies else 0.0,
                    "meanMembers": round(float(np.mean([len(colony.member_ids) for colony in active_colonies])), 3) if active_colonies else 0.0,
                    "details": [asdict(colony) for colony in active_colonies],
                },
                "structuralAdaptations": {
                    "definition": "Mutation metrics represent structural adaptation events, not a genetic mutation operator.",
                    "total": sum(count for kind, count in self.event_totals.items() if kind != "SESSION_STARTED"),
                    "prototypeUpdateOperations": sum(cell.age_steps for cell in resident_cells),
                    "byType": {kind: count for kind, count in sorted(self.event_totals.items()) if kind != "SESSION_STARTED"},
                    "history": self.structural_history,
                },
                "drawAndAudit": {
                    "trials": len(self.audit_history),
                    "agreements": agreement_count,
                    "disagreements": len(self.audit_history) - agreement_count,
                    "agreementRate": round(agreement_rate, 4) if agreement_rate is not None else None,
                    "auditorLabels": labels,
                    "results": self.audit_history,
                },
                "hiddenEvaluation": hidden_evaluation,
            },
            "recommendations": recommendations,
            "stateSnapshot": state,
            "limitations": [
                "The resource score is a compute proxy, not measured physical energy in watts.",
                "Basic shapes are a controlled initial benchmark, not a camera-vision result.",
                "Structural mutations are adaptation events; the current engine has no genetic mutation operator.",
                "Dormancy reduces prototype updates but retains resident prototype memory; memoryBytesProxy therefore includes dormant organisms.",
                "Archival requires long inactivity, sustained low value, redundancy, and non-positive replay-buffer ablation.",
                "Recommendations are deterministic heuristics for experimentation, not proof of causal improvement.",
                "The current hidden evaluation reports purity only; standard NMI and ARI remain planned.",
            ],
        }
