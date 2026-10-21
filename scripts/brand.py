from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
TOKENS_PATH = ROOT / "assets" / "brand-tokens.json"
HEX_COLOR = re.compile(r"^[0-9A-F]{6}$")


class Composition(str, Enum):
    TITLE = "title"
    INTRO = "intro"
    CONTENT = "content"
    FREEFORM = "freeform"
    FEATURE_GRID = "feature-grid"
    TWO_COLUMN = "two-column"
    SECTION = "section"
    AGENDA = "agenda"
    PHOTOS = "photos"
    PHOTO_RIGHT = "photo-right"
    CLOSING = "closing"
    TABLE = "table"
    CHART = "chart"
    TIMELINE = "timeline"


@dataclass(frozen=True)
class LayoutSpec:
    name: str
    footer: bool
    footer_region: tuple[float, float, float, float] | None
    placeholders: Mapping[str, int]
    speaker_slots: tuple[Mapping[str, int], ...]
    picture_slots: tuple[int, ...]
    picture_regions: tuple[tuple[float, float, float, float], ...]


@dataclass(frozen=True)
class PatternSpec:
    name: str
    layout: LayoutSpec
    composition: Composition
    aliases: tuple[str, ...]
    required: tuple[str, ...]
    item_limit: int | None
    image_count: int | None
    speaker_count: int | None


@dataclass(frozen=True)
class NormalizedSlide:
    pattern: PatternSpec
    data: Mapping[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


class BrandSystem:
    def __init__(self, raw: Mapping[str, Any]):
        self.raw = MappingProxyType(dict(raw))
        self.core = MappingProxyType(dict(raw["core"]))
        self.secondary = MappingProxyType(dict(raw["secondary"]))
        self.colors = MappingProxyType({**self.core, **self.secondary})
        self.fonts = MappingProxyType(dict(raw["fonts"]))
        self.type_scale = MappingProxyType(dict(raw["type_scale_pt"]))
        self.limits = MappingProxyType(dict(raw["limits"]))
        self.footer = MappingProxyType(dict(raw["footer"]))
        self.regions = MappingProxyType(
            {name: tuple(values) for name, values in raw["regions"].items()}
        )
        self.stacks = MappingProxyType(
            {
                name: MappingProxyType(
                    {
                        key: tuple(value) if isinstance(value, list) else value
                        for key, value in entry.items()
                    }
                )
                for name, entry in raw["stacks"].items()
            }
        )
        self.chart_series = tuple(raw["chart_series"])
        self.layouts = MappingProxyType(self._load_layouts(raw["template_layouts"]))
        self.patterns = MappingProxyType(self._load_patterns(raw["patterns"]))
        self._patterns_by_alias = MappingProxyType(self._build_aliases())
        self._validate()

    def _load_layouts(self, entries: Mapping[str, Any]) -> dict[str, LayoutSpec]:
        layouts: dict[str, LayoutSpec] = {}
        for name, entry in entries.items():
            footer_region = entry.get("footer_region")
            if entry["footer"] and footer_region is None:
                footer_region = [
                    self.footer["left_in"],
                    self.footer["top_in"],
                    self.footer["width_in"],
                    self.footer["height_in"],
                ]
            layouts[name] = LayoutSpec(
                name=name,
                footer=bool(entry["footer"]),
                footer_region=tuple(footer_region) if footer_region else None,
                placeholders=MappingProxyType(dict(entry.get("placeholders") or {})),
                speaker_slots=tuple(
                    MappingProxyType(dict(slot))
                    for slot in entry.get("speaker_slots") or []
                ),
                picture_slots=tuple(entry.get("picture_slots") or []),
                picture_regions=tuple(
                    tuple(region) for region in entry.get("picture_regions") or []
                ),
            )
        return layouts

    def _load_patterns(self, entries: Mapping[str, Any]) -> dict[str, PatternSpec]:
        patterns: dict[str, PatternSpec] = {}
        for name, entry in entries.items():
            layout_name = entry["layout"]
            layout = self.layouts.get(layout_name)
            if layout is None:
                raise ValueError(f"Pattern {name!r} uses unknown layout {layout_name!r}")
            patterns[name] = PatternSpec(
                name=name,
                layout=layout,
                composition=Composition(entry["composition"]),
                aliases=tuple(entry.get("aliases") or []),
                required=tuple(entry.get("required") or []),
                item_limit=entry.get("item_limit"),
                image_count=entry.get("image_count"),
                speaker_count=entry.get("speaker_count"),
            )
        return patterns

    def _build_aliases(self) -> dict[str, PatternSpec]:
        aliases: dict[str, PatternSpec] = {}
        for pattern in self.patterns.values():
            for alias in (pattern.name, *pattern.aliases):
                key = alias.strip().lower()
                if key in aliases:
                    raise ValueError(f"Duplicate layout alias {alias!r}")
                aliases[key] = pattern
            aliases.setdefault(pattern.layout.name.strip().lower(), pattern)
        return aliases

    def _validate(self) -> None:
        for name, value in self.colors.items():
            if not HEX_COLOR.fullmatch(value):
                raise ValueError(f"Color {name!r} has invalid hex {value!r}")
        for name, values in self.regions.items():
            if len(values) != 4 or any(float(value) < 0 for value in values):
                raise ValueError(f"Region {name!r} must contain four non-negative values")
        for value in self.chart_series:
            if value.upper() not in {color.upper() for color in self.colors.values()}:
                raise ValueError(f"Chart color {value!r} is not a named brand color")
        for layout in self.layouts.values():
            expected = len(layout.speaker_slots) or len(layout.picture_slots)
            if expected != len(layout.picture_regions):
                raise ValueError(
                    f"Layout {layout.name!r} has {expected} picture slots and "
                    f"{len(layout.picture_regions)} picture regions"
                )

    def resolve_pattern(self, name: str) -> PatternSpec:
        key = name.strip().lower()
        pattern = self._patterns_by_alias.get(key)
        if pattern is None:
            choices = ", ".join(sorted(self.patterns))
            raise ValueError(f"Unknown layout {name!r}. Use one of: {choices}")
        return pattern

    def color_hex(self, name_or_hex: str) -> str:
        token = name_or_hex.strip().lstrip("#").lower().replace(" ", "_")
        if token in self.colors:
            return self.colors[token]
        value = token.upper()
        if value not in {color.upper() for color in self.colors.values()}:
            choices = ", ".join(sorted(self.colors))
            raise ValueError(
                f"Off-brand color {name_or_hex!r}. Use a named token: {choices}"
            )
        return value

    def region(self, name: str) -> tuple[float, float, float, float]:
        try:
            return self.regions[name]
        except KeyError as exc:
            raise ValueError(f"Unknown brand region {name!r}") from exc

    def stack_region(
        self, stack_name: str, element: str, index: int
    ) -> tuple[float, float, float, float]:
        try:
            stack = self.stacks[stack_name]
            left, top, width, height = stack[element]
            return (
                left + float(stack.get("step_x") or 0) * index,
                top + float(stack.get("step_y") or 0) * index,
                width,
                height,
            )
        except KeyError as exc:
            raise ValueError(
                f"Unknown stack region {stack_name!r}.{element}"
            ) from exc

    def normalize_slide(self, spec: Mapping[str, Any]) -> NormalizedSlide:
        data = dict(spec)
        requested = data.get("layout") or data.get("intent") or "content"
        pattern = self.resolve_pattern(str(requested))
        data["layout"] = pattern.name
        data["title"] = data.get("title") or data.get("statement")
        data["subtitle"] = data.get("subtitle") or data.get("subhead")
        if pattern.composition == Composition.CONTENT:
            bullets = data.get("bullets") or data.get("body")
            data["bullets"] = [bullets] if isinstance(bullets, str) else bullets
        if pattern.composition in {
            Composition.TWO_COLUMN,
            Composition.FEATURE_GRID,
            Composition.PHOTO_RIGHT,
            Composition.AGENDA,
            Composition.TIMELINE,
        }:
            items = data.get("items") or data.get("right") or []
            if isinstance(items, Mapping):
                items = items.get("items") or []
            data["items"] = list(items)
        if pattern.composition == Composition.INTRO:
            speakers = data.get("speakers")
            if speakers is None and any(
                data.get(key)
                for key in (
                    "name",
                    "role",
                    "company",
                    "org",
                    "image",
                    "title",
                    "subtitle",
                )
            ):
                speakers = [
                    {
                        "name": data.get("name") or data.get("title") or "",
                        "role": data.get("role") or data.get("subtitle") or "",
                        "company": data.get("company") or data.get("org") or "",
                        "image": data.get("image"),
                    }
                ]
            data["speakers"] = list(speakers or [])
        if pattern.composition == Composition.PHOTOS:
            images = data.get("images")
            if images is None and data.get("image"):
                images = [data["image"]]
            data["images"] = list(images or [])
        self._validate_slide(pattern, data)
        return NormalizedSlide(pattern=pattern, data=MappingProxyType(data))

    def normalize_outline(
        self, outline: Mapping[str, Any]
    ) -> tuple[NormalizedSlide, ...]:
        return tuple(self.normalize_slide(spec) for spec in outline.get("slides") or [])

    def _validate_slide(self, pattern: PatternSpec, data: Mapping[str, Any]) -> None:
        missing = [field for field in pattern.required if not data.get(field)]
        if missing:
            fields = ", ".join(missing)
            raise ValueError(f"{pattern.name} needs: {fields}")
        if pattern.item_limit is not None:
            items = data.get("items") or []
            if len(items) > pattern.item_limit:
                raise ValueError(
                    f"{pattern.name} allows at most {pattern.item_limit} items"
                )
        if pattern.image_count is not None:
            images = data.get("images") or []
            if len(images) != pattern.image_count:
                raise ValueError(
                    f"{pattern.name} needs exactly {pattern.image_count} images"
                )
        if pattern.speaker_count is not None:
            speakers = data.get("speakers") or []
            if len(speakers) != pattern.speaker_count:
                raise ValueError(
                    f"{pattern.name} needs exactly {pattern.speaker_count} speakers"
                )


def load_brand(path: Path = TOKENS_PATH) -> BrandSystem:
    return BrandSystem(json.loads(path.read_text()))


def load_outline(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required for YAML outlines") from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("slides"), list):
        raise ValueError("Outline must contain a top-level slides list")
    return data


BRAND = load_brand()
