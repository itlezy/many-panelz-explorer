"""Built-in color schemes and runtime token resolution."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Final, cast

from PySide6.QtGui import QColor

from ._settings import normalize

COLOR_SCHEME_COMMANDER_CLASSIC: Final[str] = "commander_classic"
COLOR_SCHEME_CURRENT_LEGACY: Final[str] = "current_legacy"
COLOR_SCHEME_LOW_GLARE: Final[str] = "low_glare"


@dataclass(frozen=True, slots=True)
class ResolvedColorScheme:
    """Store one fully resolved runtime color scheme."""

    scheme_id: str
    file_list_background_hex: str
    file_list_current_focused_background_hex: str
    file_list_current_inactive_background_hex: str
    file_list_marked_background_hex: str
    file_list_marked_text_hex: str
    file_list_current_marked_focused_background_hex: str
    file_list_current_marked_inactive_background_hex: str
    file_list_current_marked_text_hex: str
    file_list_hidden_text_hex: str
    panel_surface_background_hex: str
    toolbar_background_hex: str
    toolbar_text_hex: str
    footer_background_hex: str
    footer_text_hex: str
    tab_active_background_hex: str
    tab_active_text_hex: str
    tab_inactive_background_hex: str
    tab_inactive_text_hex: str
    active_panel_tint_color_hex: str
    active_panel_tint_intensity_percent: int
    target_panel_tint_color_hex: str
    target_panel_tint_intensity_percent: int


_PRESET_LABELS: Final[dict[str, str]] = {
    COLOR_SCHEME_COMMANDER_CLASSIC: "Commander Classic",
    COLOR_SCHEME_CURRENT_LEGACY: "Current Legacy",
    COLOR_SCHEME_LOW_GLARE: "Low Glare",
}


_PRESETS: Final[dict[str, ResolvedColorScheme]] = {
    COLOR_SCHEME_COMMANDER_CLASSIC: ResolvedColorScheme(
        scheme_id=COLOR_SCHEME_COMMANDER_CLASSIC,
        file_list_background_hex="#F6F0E3",
        file_list_current_focused_background_hex="#E1D9C7",
        file_list_current_inactive_background_hex="#ECE5D7",
        file_list_marked_background_hex="#D4C486",
        file_list_marked_text_hex="#2A2415",
        file_list_current_marked_focused_background_hex="#C9B261",
        file_list_current_marked_inactive_background_hex="#D7C786",
        file_list_current_marked_text_hex="#1E1A10",
        file_list_hidden_text_hex="#7C786C",
        panel_surface_background_hex="#E8E0D0",
        toolbar_background_hex="#DDD2BE",
        toolbar_text_hex="#2B2924",
        footer_background_hex="#D7CCB5",
        footer_text_hex="#2D2A22",
        tab_active_background_hex="#F1E6CE",
        tab_active_text_hex="#241F16",
        tab_inactive_background_hex="#CFC3AF",
        tab_inactive_text_hex="#4C453B",
        active_panel_tint_color_hex="#A8B6C4",
        active_panel_tint_intensity_percent=24,
        target_panel_tint_color_hex="#D2CCAA",
        target_panel_tint_intensity_percent=28,
    ),
    COLOR_SCHEME_CURRENT_LEGACY: ResolvedColorScheme(
        scheme_id=COLOR_SCHEME_CURRENT_LEGACY,
        file_list_background_hex="#FFFFFF",
        file_list_current_focused_background_hex="#E7EDF4",
        file_list_current_inactive_background_hex="#F1F4F7",
        file_list_marked_background_hex="#C5D1DB",
        file_list_marked_text_hex="#1E252B",
        file_list_current_marked_focused_background_hex="#B7C8D8",
        file_list_current_marked_inactive_background_hex="#C6D2DE",
        file_list_current_marked_text_hex="#1A2129",
        file_list_hidden_text_hex="#7F8993",
        panel_surface_background_hex="#F7F8FA",
        toolbar_background_hex="#F2F4F7",
        toolbar_text_hex="#21262C",
        footer_background_hex="#EDF1F5",
        footer_text_hex="#232A32",
        tab_active_background_hex="#FFFFFF",
        tab_active_text_hex="#1E242A",
        tab_inactive_background_hex="#E5EAF0",
        tab_inactive_text_hex="#4A5460",
        active_panel_tint_color_hex="#A8B6C4",
        active_panel_tint_intensity_percent=24,
        target_panel_tint_color_hex="#D2CCAA",
        target_panel_tint_intensity_percent=28,
    ),
    COLOR_SCHEME_LOW_GLARE: ResolvedColorScheme(
        scheme_id=COLOR_SCHEME_LOW_GLARE,
        file_list_background_hex="#EAE7DF",
        file_list_current_focused_background_hex="#D2D0C7",
        file_list_current_inactive_background_hex="#DDD9D0",
        file_list_marked_background_hex="#BFAE78",
        file_list_marked_text_hex="#221E15",
        file_list_current_marked_focused_background_hex="#AE9757",
        file_list_current_marked_inactive_background_hex="#BDAA6D",
        file_list_current_marked_text_hex="#18150E",
        file_list_hidden_text_hex="#777267",
        panel_surface_background_hex="#D9D5CC",
        toolbar_background_hex="#CDC7BC",
        toolbar_text_hex="#26231D",
        footer_background_hex="#C4BDAE",
        footer_text_hex="#2A261F",
        tab_active_background_hex="#E2DBCF",
        tab_active_text_hex="#201C15",
        tab_inactive_background_hex="#BCB4A7",
        tab_inactive_text_hex="#4A443A",
        active_panel_tint_color_hex="#8098AA",
        active_panel_tint_intensity_percent=26,
        target_panel_tint_color_hex="#BDAF7B",
        target_panel_tint_intensity_percent=30,
    ),
}

COLOR_SCHEME_COLOR_KEYS: Final[tuple[str, ...]] = (
    "file_list_background_hex",
    "file_list_current_focused_background_hex",
    "file_list_current_inactive_background_hex",
    "file_list_marked_background_hex",
    "file_list_marked_text_hex",
    "file_list_current_marked_focused_background_hex",
    "file_list_current_marked_inactive_background_hex",
    "file_list_current_marked_text_hex",
    "file_list_hidden_text_hex",
    "panel_surface_background_hex",
    "toolbar_background_hex",
    "toolbar_text_hex",
    "footer_background_hex",
    "footer_text_hex",
    "tab_active_background_hex",
    "tab_active_text_hex",
    "tab_inactive_background_hex",
    "tab_inactive_text_hex",
    "active_panel_tint_color_hex",
    "target_panel_tint_color_hex",
)
COLOR_SCHEME_INT_KEYS: Final[tuple[str, ...]] = (
    "active_panel_tint_intensity_percent",
    "target_panel_tint_intensity_percent",
)
ALLOWED_COLOR_SCHEME_IDS: Final[set[str]] = set(_PRESET_LABELS)


def color_scheme_label(scheme_id: str) -> str:
    """Return the user-facing label for one scheme identifier."""

    return _PRESET_LABELS.get(scheme_id, _PRESET_LABELS[COLOR_SCHEME_COMMANDER_CLASSIC])


def color_scheme_ids() -> tuple[str, ...]:
    """Return the built-in scheme identifiers in display order."""

    return (
        COLOR_SCHEME_COMMANDER_CLASSIC,
        COLOR_SCHEME_CURRENT_LEGACY,
        COLOR_SCHEME_LOW_GLARE,
    )


def default_color_scheme() -> ResolvedColorScheme:
    """Return the default built-in color scheme."""

    return _PRESETS[COLOR_SCHEME_COMMANDER_CLASSIC]


def normalize_color_scheme_id(raw: object, *, fallback: str) -> str:
    """Normalize a raw scheme id into a supported built-in preset id."""

    candidate = str(raw or "").strip().lower()
    if candidate in ALLOWED_COLOR_SCHEME_IDS:
        return candidate
    return fallback


def normalize_color_scheme_overrides_json(raw: object, *, fallback: str) -> str:
    """Normalize scheme override JSON into a canonical subset."""

    text = str(raw or "").strip()
    if not text:
        return str(fallback)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return str(fallback)
    if not isinstance(payload, dict):
        return str(fallback)
    raw_mapping = cast("dict[object, object]", payload)
    normalized_payload: dict[str, str | int] = {}
    for key, value in raw_mapping.items():
        normalized_key = str(key or "").strip()
        if normalized_key in COLOR_SCHEME_COLOR_KEYS:
            preset_value = getattr(default_color_scheme(), normalized_key)
            normalized_payload[normalized_key] = normalize.normalize_color_hex(
                value,
                fallback=str(preset_value),
            )
            continue
        if normalized_key in COLOR_SCHEME_INT_KEYS:
            preset_value = getattr(default_color_scheme(), normalized_key)
            normalized_payload[normalized_key] = normalize.normalize_percent(
                value,
                fallback=int(preset_value),
            )
    return json.dumps(normalized_payload, sort_keys=True)


def resolve_color_scheme(
    *,
    scheme_id: str,
    overrides_json: str,
    active_panel_tint_color_hex: str,
    active_panel_tint_intensity_percent: int,
    target_panel_tint_color_hex: str,
    target_panel_tint_intensity_percent: int,
) -> ResolvedColorScheme:
    """Resolve one built-in preset plus any overrides into runtime tokens."""

    normalized_id = normalize_color_scheme_id(
        scheme_id,
        fallback=COLOR_SCHEME_COMMANDER_CLASSIC,
    )
    payload = asdict(_PRESETS[normalized_id])
    normalized_json = normalize_color_scheme_overrides_json(
        overrides_json,
        fallback="{}",
    )
    overrides = json.loads(normalized_json)
    payload.update(overrides)
    payload["scheme_id"] = normalized_id
    # Keep legacy tint controls as high-priority explicit overrides.
    payload["active_panel_tint_color_hex"] = normalize.normalize_color_hex(
        active_panel_tint_color_hex,
        fallback=str(payload["active_panel_tint_color_hex"]),
    )
    payload["active_panel_tint_intensity_percent"] = normalize.normalize_percent(
        active_panel_tint_intensity_percent,
        fallback=int(payload["active_panel_tint_intensity_percent"]),
    )
    payload["target_panel_tint_color_hex"] = normalize.normalize_color_hex(
        target_panel_tint_color_hex,
        fallback=str(payload["target_panel_tint_color_hex"]),
    )
    payload["target_panel_tint_intensity_percent"] = normalize.normalize_percent(
        target_panel_tint_intensity_percent,
        fallback=int(payload["target_panel_tint_intensity_percent"]),
    )
    return ResolvedColorScheme(**payload)


def blended_color_hex(
    base_hex: str,
    overlay_hex: str,
    *,
    overlay_percent: int,
) -> str:
    """Return an opaque blend between a base and overlay color."""

    base = QColor(base_hex)
    overlay = QColor(overlay_hex)
    if not base.isValid():
        base = QColor(default_color_scheme().panel_surface_background_hex)
    if not overlay.isValid():
        overlay = QColor(default_color_scheme().active_panel_tint_color_hex)
    weight = max(0.0, min(1.0, float(overlay_percent) / 100.0))
    inverse_weight = 1.0 - weight
    blended = QColor(
        round((base.red() * inverse_weight) + (overlay.red() * weight)),
        round((base.green() * inverse_weight) + (overlay.green() * weight)),
        round((base.blue() * inverse_weight) + (overlay.blue() * weight)),
    )
    return blended.name(QColor.NameFormat.HexRgb).upper()
