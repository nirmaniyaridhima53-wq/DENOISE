# ui_theme.py
# Shared visual theme helpers for all pages (logo watermark, branding)

import base64
from pathlib import Path

import streamlit as st

# Logo lives at: pdf-study-copilot/assets/logo.png
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()


def _logo_watermark_uri(opacity: float) -> str:
    """
    Wrap the logo PNG inside an SVG that carries the opacity,
    then return it as a base64 data URI (no external URL needed).
    """
    with open(LOGO_PATH, "rb") as f:
        png_b64 = base64.b64encode(f.read()).decode("utf-8")

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" '
        f'opacity="{opacity}">'
        f'<image href="data:image/png;base64,{png_b64}" '
        'width="900" height="900" preserveAspectRatio="xMidYMid meet"/>'
        "</svg>"
    )

    svg_b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_b64}"


def inject_logo_watermark(opacity: float = 0.06, size: str = "60vmin"):
    """
    Add a faded, centered logo BEHIND all page content.

    opacity: 0.04 = very faint | 0.06 = subtle (default) | 0.10 = clearly visible
    size:    CSS background-size, e.g. "60vmin", "450px", "cover"
    """
    if not HAS_LOGO:
        return

    uri = _logo_watermark_uri(opacity)

    st.markdown(
        f"""
        <style>
        .stApp, [data-testid="stAppViewContainer"] {{
            background-image: url("{uri}");
            background-repeat: no-repeat;
            background-position: center center;
            background-size: {size};
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
