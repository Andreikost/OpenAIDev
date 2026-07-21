from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .core import SHAPES, ColonyMindEngine


BASE_SHAPES = tuple(SHAPES)
SUPPORTED_EXPERIMENT_SHAPES = (*BASE_SHAPES, "pentagon", "star", "cross")
ExperimentShape = Literal["circle", "triangle", "square", "pentagon", "star", "cross"]


class VariantModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KernelParameterOverrides(VariantModel):
    """Allowlisted learning-policy changes with deliberately conservative bounds."""

    organismBirthNovelty: float | None = Field(default=None, ge=0.010, le=0.040)
    cellBirthNovelty: float | None = Field(default=None, ge=0.010, le=0.040)
    digestionError: float | None = Field(default=None, ge=0.015, le=0.050)
    memoryEvidenceRequired: float | None = Field(default=None, ge=6.0, le=30.0)
    microNoveltyThreshold: float | None = Field(default=None, ge=0.010, le=0.040)
    microSupportRequired: int | None = Field(default=None, ge=2, le=12)
    intermediateBirthNovelty: float | None = Field(default=None, ge=0.010, le=0.040)
    replayCapacity: int | None = Field(default=None, ge=32, le=256)

    def applied(self) -> dict[str, float | int]:
        return self.model_dump(exclude_none=True)


class KernelVariantSpec(VariantModel):
    """A declarative, reproducible copy of the frozen learning kernel.

    GPT may populate only these fields. No source text, import, command, or
    executable expression can cross this schema boundary.
    """

    mode: Literal["baseline_copy", "derived_copy"] = "baseline_copy"
    shapes: list[ExperimentShape] = Field(default_factory=lambda: list(BASE_SHAPES), min_length=3, max_length=6)
    parameterOverrides: KernelParameterOverrides = Field(default_factory=KernelParameterOverrides)
    mechanisms: list[Literal["adaptive_novelty_schedule", "memory_gated_growth"]] = Field(default_factory=list, max_length=2)
    changeSummary: list[str] = Field(
        default_factory=lambda: ["Run an isolated copy of the immutable baseline kernel."],
        min_length=1,
        max_length=8,
    )

    @model_validator(mode="after")
    def normalize_copy(self) -> "KernelVariantSpec":
        ordered: list[str] = []
        for shape in (*BASE_SHAPES, *self.shapes):
            if shape not in ordered:
                ordered.append(shape)
        self.shapes = ordered[:6]  # type: ignore[assignment]
        if self.parameterOverrides.applied() or self.mechanisms or tuple(self.shapes) != BASE_SHAPES:
            self.mode = "derived_copy"
        return self

    def spec_hash(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


PARAMETER_ATTRIBUTES = {
    "organismBirthNovelty": "organism_birth_novelty",
    "cellBirthNovelty": "cell_birth_novelty",
    "digestionError": "digestion_error",
    "memoryEvidenceRequired": "memory_evidence_required",
    "microNoveltyThreshold": "micro_novelty_threshold",
    "microSupportRequired": "micro_support_required",
    "intermediateBirthNovelty": "intermediate_birth_novelty",
    "replayCapacity": "replay_capacity",
}


def variant_source_sha256() -> str:
    normalized = Path(__file__).read_text(encoding="utf-8").replace("\r\n", "\n").encode()
    return hashlib.sha256(normalized).hexdigest()


class VariantColonyMindEngine(ColonyMindEngine):
    """Independent engine copy with an allowlisted, fingerprinted change set."""

    def __init__(self, seed: int, variant: KernelVariantSpec) -> None:
        self.variant = variant
        self.shape_vocabulary = tuple(variant.shapes)
        super().__init__(seed)
        # Keep retinal sampling independent from structural RNG consumption so
        # variant and matched-control arms receive identical input streams.
        self.stimulus_rng = random.Random(f"{seed}:colonymind-variant-stimulus")
        for public_name, value in variant.parameterOverrides.applied().items():
            setattr(self, PARAMETER_ATTRIBUTES[public_name], value)
        self._variant_policy_base = {
            "organismBirthNovelty": float(self.organism_birth_novelty),
            "cellBirthNovelty": float(self.cell_birth_novelty),
            "microNoveltyThreshold": float(self.micro_novelty_threshold),
            "intermediateBirthNovelty": float(self.intermediate_birth_novelty),
        }

    def _apply_allowlisted_mechanisms(self) -> None:
        if "adaptive_novelty_schedule" in self.variant.mechanisms:
            progress = min(1.0, self.step_count / 1_440.0)
            self.micro_novelty_threshold = self._variant_policy_base["microNoveltyThreshold"] * (1.0 - 0.18 * progress)
            self.intermediate_birth_novelty = self._variant_policy_base["intermediateBirthNovelty"] * (1.0 - 0.12 * progress)
        if "memory_gated_growth" in self.variant.mechanisms:
            saturation = min(1.0, len(self.memories) / 8.0)
            self.organism_birth_novelty = self._variant_policy_base["organismBirthNovelty"] * (1.0 + 0.60 * saturation)
            self.cell_birth_novelty = self._variant_policy_base["cellBirthNovelty"] * (1.0 + 0.40 * saturation)

    def step(self, count: int = 1) -> dict[str, Any]:
        self._apply_allowlisted_mechanisms()
        return super().step(count)

    @staticmethod
    def _inside_extended(shape: str, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        absolute_x = np.abs(x)
        absolute_y = np.abs(y)
        if shape == "cross":
            return ((absolute_x <= 0.25) & (absolute_y <= 0.84)) | ((absolute_y <= 0.25) & (absolute_x <= 0.84))

        radius = np.hypot(x, y)
        angle = np.arctan2(y, x) + math.pi / 2.0
        if shape == "pentagon":
            sides = 5
            half_sector = math.pi / sides
            local_angle = (angle + half_sector) % (2.0 * half_sector) - half_sector
            boundary = 0.82 * math.cos(half_sector) / np.cos(local_angle)
            return radius <= boundary
        if shape == "star":
            boundary = 0.48 + 0.34 * (0.5 + 0.5 * np.cos(5.0 * angle))
            return radius <= boundary
        raise ValueError(f"Unknown experimental visual generator shape: {shape}")

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
        if shape in BASE_SHAPES:
            return super()._retina_for(
                shape,
                rotation,
                scale,
                noise,
                occlusion,
                offset_x,
                offset_y,
                rng,
                render_mode,
            )
        if shape not in self.shape_vocabulary:
            raise ValueError(f"Shape is not enabled for this variant: {shape}")
        if render_mode not in {"filled", "outline"}:
            raise ValueError(f"Unknown retinal render mode: {render_mode}")

        source_rng = rng or self.rng
        cosine = math.cos(rotation)
        sine = math.sin(rotation)
        coverage = np.zeros((self.retina_side, self.retina_side), dtype=np.float64)
        columns, rows = np.meshgrid(
            np.arange(self.retina_side, dtype=np.float64),
            np.arange(self.retina_side, dtype=np.float64),
        )

        def inside(local_x: np.ndarray, local_y: np.ndarray) -> np.ndarray:
            return self._inside_extended(shape, local_x, local_y)

        for subpixel_y in (-0.25, 0.25):
            for subpixel_x in (-0.25, 0.25):
                retinal_x = ((columns + 0.5 + subpixel_x) / self.retina_side) * 2.0 - 1.0 - offset_x
                retinal_y = ((rows + 0.5 + subpixel_y) / self.retina_side) * 2.0 - 1.0 - offset_y
                local_x = (cosine * retinal_x + sine * retinal_y) / scale
                local_y = (-sine * retinal_x + cosine * retinal_y) / scale
                outer = inside(local_x, local_y)
                coverage += outer & ~inside(local_x / 0.84, local_y / 0.84) if render_mode == "outline" else outer

        signal = 0.025 + (coverage / 4.0) * 0.915
        noise_values = np.fromiter(
            (source_rng.uniform(-noise, noise) for _ in range(self.vector_size)),
            dtype=np.float64,
            count=self.vector_size,
        ).reshape((self.retina_side, self.retina_side)) if noise > 0.0 else np.zeros_like(coverage)
        pixels = signal + noise_values
        if occlusion > 0:
            span = max(1, min(self.retina_side - 1, round(self.retina_side * math.sqrt(occlusion))))
            start_row = source_rng.randrange(0, self.retina_side - span + 1)
            start_column = source_rng.randrange(0, self.retina_side - span + 1)
            pixels[start_row : start_row + span, start_column : start_column + span] *= 0.10
        return np.clip(pixels.reshape(self.vector_size), 0.0, 1.0)

    def _sample(self) -> tuple[np.ndarray, dict[str, Any], str]:
        source_rng = self.stimulus_rng
        shape = source_rng.choice(self.shape_vocabulary)
        rotation = source_rng.uniform(-math.pi, math.pi)
        scale = source_rng.uniform(0.38, 0.82)
        noise = source_rng.uniform(0.008, 0.14)
        occlusion = source_rng.choice((0.0, 0.0, 0.10, 0.18, 0.25))
        offset_limit = max(0.04, (1.0 - scale) * 0.34)
        offset_x = source_rng.uniform(-offset_limit, offset_limit)
        offset_y = source_rng.uniform(-offset_limit, offset_limit)
        render_mode = source_rng.choice(("filled", "outline"))
        vector = self._retina_for(
            shape,
            rotation,
            scale,
            noise,
            occlusion,
            offset_x,
            offset_y,
            rng=source_rng,
            render_mode=render_mode,
        )
        public = {
            "id": self._next_id("sample"),
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
        return vector, public, shape


def create_variant_engine(seed: int, variant: KernelVariantSpec) -> VariantColonyMindEngine:
    return VariantColonyMindEngine(seed, variant)
