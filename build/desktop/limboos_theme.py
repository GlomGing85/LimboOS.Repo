#!/usr/bin/env python3
# ==============================================================================
# LimboOS Theme Engine v1.0
# Centralized color scheme and styling for the LimboOS Desktop Environment
# ==============================================================================

# Color Palette - Retro Cyber Teal Theme
COLORS = {
    # Primary
    "bg_primary": "#008080",       # Desktop teal background
    "bg_dark": "#001830",          # Dark blue header
    "bg_panel": "#1F2428",         # Taskbar / panels
    "bg_window": "#2D333B",        # Window backgrounds
    "bg_input": "#1A1D20",         # Input fields / text areas
    "bg_input_dark": "#101418",    # Darker input fields

    # Accents
    "accent_teal": "#00FFFF",      # Cyan/teal highlights
    "accent_green": "#55FF55",     # Status green
    "accent_yellow": "#FFFF00",    # Warnings / highlights
    "accent_red": "#FF5555",       # Errors / danger
    "accent_blue": "#006699",      # Buttons

    # Text
    "text_white": "#FFFFFF",
    "text_light": "#AAAAAA",
    "text_dim": "#888888",
    "text_cyan": "#00FFFF",
    "text_green": "#55FF55",

    # Buttons
    "btn_start": "#006699",        # Start menu button
    "btn_action": "#008080",       # Action buttons (teal)
    "btn_danger": "#800000",       # Danger / remove
    "btn_tab": "#004080",          # Window tabs
    "btn_header": "#004080",       # Headers

    # Desktop icons
    "icon_bg": "#006060",
    "icon_active": "#00A0A0",
}

# Font settings
FONTS = {
    "title": ("Sans", 13, "bold"),
    "header": ("Sans", 11, "bold"),
    "body": ("Sans", 10),
    "body_bold": ("Sans", 10, "bold"),
    "small": ("Sans", 9),
    "small_bold": ("Sans", 9, "bold"),
    "mono": ("Monospace", 10),
    "mono_bold": ("Monospace", 10, "bold"),
    "mono_large": ("Monospace", 14, "bold"),
    "display": ("Monospace", 18, "bold"),
}

# Window defaults
WINDOW_DEFAULTS = {
    "width": 580,
    "height": 420,
    "bg": COLORS["bg_window"],
}

# ASCII Banner
ASCII_BANNER = """\
 __    _       _          _____ _____
|  |  |_|_____| |_ ___   |     |   __|
|  |__| |     | . | . |  |  |  |__   |
|_____|_|_|_|_|___|___|  |_____|_____|\
"""

def get_color(name):
    """Get a color by name from the palette."""
    return COLORS.get(name, "#FFFFFF")

def get_font(name):
    """Get a font tuple by name."""
    return FONTS.get(name, FONTS["body"])
