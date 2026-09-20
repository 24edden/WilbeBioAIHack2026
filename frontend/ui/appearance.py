"""One light/dark preference and one palette for the entire frontend."""
from pathlib import Path

PALETTES = {
    "light": {
        "page":"#f7fafb", "surface":"#ffffff", "soft":"#eff5f5", "hover":"#e7f1ee",
        "text":"#294650", "secondary":"#4f6874", "muted":"#59727d", "border":"#d7e3e7",
        "accent":"#34796b", "accent-hover":"#286357", "on-accent":"#ffffff",
        "focus":"#76b6a8", "halo":"#eaf2ee", "shadow":"#173e4708",
        "good":"#27734e", "warning":"#976219", "critical":"#b34758",
    },
    "dark": {
        "page":"#101e27", "surface":"#192c36", "soft":"#203640", "hover":"#29434b",
        "text":"#e2edf1", "secondary":"#b4c7cf", "muted":"#92abb6", "border":"#344c57",
        "accent":"#88cbb7", "accent-hover":"#a1ddca", "on-accent":"#153b34",
        "focus":"#8ad2c0", "halo":"#284039", "shadow":"#00000020",
        "good":"#8bd1a6", "warning":"#e3bd73", "critical":"#f1a0ac",
    },
}


def palette(theme):
    return dict(PALETTES["dark" if theme == "dark" else "light"])


def stylesheet(theme):
    colors = palette(theme)
    tokens = ";".join(f"--ui-{name}:{value}" for name,value in colors.items())
    mode = "dark" if theme == "dark" else "light"
    return "<style>:root,.stApp{"+tokens+f";color-scheme:{mode};"+"}" + (Path(__file__).resolve().parents[1]/"static"/"workspace.css").read_text(encoding='utf-8') + "</style>"


def toggle_theme():
    import streamlit as st
    st.session_state.ui_theme = "dark" if st.session_state.ui_theme == "light" else "light"
    # Retain the existing voice component's light/dark input without a second control.
    st.session_state.astral_theme = st.session_state.ui_theme == "light"
