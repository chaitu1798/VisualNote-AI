from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeStyle:
    name: str
    background: str
    page_bg: str
    card_bg: str
    card_border: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent: str
    accent_light: str
    font_family: str
    badge_bg: str
    badge_text: str
    formula_bg: str
    shadow: str


THEMES: Dict[str, ThemeStyle] = {
    "clean_handwritten": ThemeStyle(
        name="Clean Handwritten",
        background="#f8f9fa",
        page_bg="#ffffff",
        card_bg="#fbfbfd",
        card_border="#e2e8f0",
        text_primary="#1e293b",
        text_secondary="#475569",
        text_muted="#94a3b8",
        accent="#4f46e5",
        accent_light="#eef2ff",
        font_family="'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        badge_bg="#e0e7ff",
        badge_text="#3730a3",
        formula_bg="#f1f5f9",
        shadow="0 4px 12px rgba(0, 0, 0, 0.05)",
    ),
    "notebook": ThemeStyle(
        name="Notebook Paper",
        background="#fdfbf7",
        page_bg="#fffefb",
        card_bg="#ffffff",
        card_border="#f0eae1",
        text_primary="#2d3748",
        text_secondary="#4a5568",
        text_muted="#a0aec0",
        accent="#d97706",
        accent_light="#fef3c7",
        font_family="'Segoe UI', Roboto, -apple-system, sans-serif",
        badge_bg="#fef3c7",
        badge_text="#92400e",
        formula_bg="#faf5ee",
        shadow="0 4px 8px rgba(180, 160, 140, 0.1)",
    ),
    "chalkboard": ThemeStyle(
        name="Chalkboard Dark",
        background="#0f172a",
        page_bg="#1e293b",
        card_bg="#334155",
        card_border="#475569",
        text_primary="#f8fafc",
        text_secondary="#cbd5e1",
        text_muted="#64748b",
        accent="#38bdf8",
        accent_light="#0369a1",
        font_family="'Inter', -apple-system, sans-serif",
        badge_bg="#0284c7",
        badge_text="#f0f9ff",
        formula_bg="#1e293b",
        shadow="0 6px 16px rgba(0, 0, 0, 0.4)",
    ),
    "minimal": ThemeStyle(
        name="Clean Minimal",
        background="#ffffff",
        page_bg="#ffffff",
        card_bg="#ffffff",
        card_border="#000000",
        text_primary="#000000",
        text_secondary="#333333",
        text_muted="#666666",
        accent="#000000",
        accent_light="#f4f4f4",
        font_family="'Inter', system-ui, sans-serif",
        badge_bg="#000000",
        badge_text="#ffffff",
        formula_bg="#f4f4f4",
        shadow="none",
    ),
}


def get_theme(theme_name: str) -> ThemeStyle:
    return THEMES.get(theme_name, THEMES["clean_handwritten"])
