"""Load the dual-theme stylesheet with runtime theme tokens."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

FONT_IMPORT = (
    '@import url("https://fonts.googleapis.com/css2?'
    'family=Literata:opsz,wght@7..72,600&'
    'family=Public+Sans:wght@400;500;600;700&display=swap");'
)

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "ground": "#0B0D10",
        "panel": "#14171C",
        "panel_2": "#191E24",
        "panel_3": "#20262E",
        "line": "#2B323B",
        "line_strong": "#3D4653",
        "ink": "#F4F7FA",
        "ink_soft": "#C8D2DE",
        "muted": "#97A3B4",
        "blue": "#7AA2FF",
        "blue_deep": "#A8C0FF",
        "blue_soft": "#18243A",
        "blue_tint": "#253A5A",
        "on_blue": "#0A1224",
        "success": "#71D6A1",
        "success_soft": "#12251A",
        "success_line": "#265039",
        "warning": "#F2C56B",
        "warning_soft": "#2A2113",
        "warning_line": "#5A4721",
        "danger": "#FF9A9A",
        "danger_soft": "#2A1618",
        "danger_line": "#5B2C30",
        "user_bg": "#1B2A45",
        "user_line": "#2B4266",
        "shadow": "0 18px 40px rgba(0, 0, 0, 0.34)",
        "shadow_soft": "0 1px 2px rgba(0, 0, 0, 0.4), 0 8px 22px rgba(0, 0, 0, 0.2)",
        "scheme": "dark",
    },
    "light": {
        "ground": "#F3F5F8",
        "panel": "#FFFFFF",
        "panel_2": "#F7F9FB",
        "panel_3": "#EDF1F5",
        "line": "#E1E6ED",
        "line_strong": "#C8D1DC",
        "ink": "#111827",
        "ink_soft": "#334155",
        "muted": "#5B6778",
        "blue": "#1D4ED8",
        "blue_deep": "#1E40AF",
        "blue_soft": "#EFF4FF",
        "blue_tint": "#DCE8FF",
        "on_blue": "#FFFFFF",
        "success": "#166534",
        "success_soft": "#F0FDF4",
        "success_line": "#BBF7D0",
        "warning": "#92400E",
        "warning_soft": "#FFFBEB",
        "warning_line": "#FDE68A",
        "danger": "#B42318",
        "danger_soft": "#FEF2F2",
        "danger_line": "#FECACA",
        "user_bg": "#EFF4FF",
        "user_line": "#D7E4FB",
        "shadow": "0 18px 40px rgba(15, 23, 42, 0.08)",
        "shadow_soft": "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 22px rgba(15, 23, 42, 0.04)",
        "scheme": "light",
    },
}


def _root_block(theme: str) -> str:
    tokens = THEMES.get(theme, THEMES["dark"])
    lines = [":root {"]
    lines.append(f"  color-scheme: {tokens['scheme']};")
    for key, value in tokens.items():
        if key == "scheme":
            continue
        lines.append(f"  --{key.replace('_', '-')}: {value};")
    lines.append(f"  --background-color: {tokens['ground']};")
    lines.append(f"  --secondary-background-color: {tokens['panel']};")
    lines.append(f"  --text-color: {tokens['ink']};")
    lines.append(f"  --primary-color: {tokens['blue']};")
    lines.append("}")
    return "\n".join(lines)


def apply_theme(theme: str = "dark") -> None:
    css = Path(__file__).with_name("theme.css").read_text(encoding="utf-8")
    st.markdown(
        f"<style>{FONT_IMPORT}\n{_root_block(theme)}\n{css}</style>",
        unsafe_allow_html=True,
    )
