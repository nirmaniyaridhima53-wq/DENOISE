# ui_theme.py
# Research OS design system: tokens, fonts, animations, component styles.
# FIX: entire CSS is now wrapped in <style> tags so the browser APPLIES it
# instead of printing it as page text.

import base64
from pathlib import Path

import streamlit as st

# Logo lives at: pdf-study-copilot/assets/logo.png
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()


# ============================================================
# DESIGN SYSTEM CSS — MUST start with <style> and end with </style>
# ============================================================

DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* Surface Palette */
  --bg-app: #070913;
  --bg-surface-1: #0E1322;
  --bg-surface-2: #161D31;
  --bg-surface-hover: #1E2842;

  /* Brand & Accent */
  --accent-teal: #2DD4BF;
  --accent-teal-glow: rgba(45, 212, 191, 0.25);
  --accent-purple: #A855F7;
  --accent-purple-glow: rgba(168, 85, 247, 0.25);
  --brand-gradient: linear-gradient(135deg, var(--accent-teal) 0%, var(--accent-purple) 100%);

  /* Status Colors */
  --status-success: #10B981;
  --status-warning: #F97316;
  --status-error: #EF4444;

  /* Typography */
  --font-heading: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Roboto Mono', monospace;

  /* Text Colors */
  --text-primary: #F9FAFB;
  --text-secondary: #9CA3AF;
  --text-muted: #6B7280;

  /* Spatial Grid (8-pt) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;

  /* Motion */
  --ease-elastic: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-smooth: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 300ms;
}

/* ---------- Base surfaces ---------- */
.stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg-app);
}
[data-testid="stHeader"] {
  background: transparent;
}
body, p, li, .stMarkdown {
  font-family: var(--font-body);
  color: var(--text-primary);
}
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  color: var(--text-primary);
}
code, pre {
  font-family: var(--font-mono);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
  background: var(--bg-surface-1);
  border-right: 1px solid rgba(255,255,255,0.06);
}

/* ---------- Buttons ---------- */
div.stButton > button {
  background: var(--bg-surface-2);
  color: var(--text-primary);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  font-family: var(--font-body);
  font-weight: 600;
  transition: transform var(--duration-fast) var(--ease-smooth),
              box-shadow var(--duration-fast) var(--ease-smooth),
              border-color var(--duration-fast) var(--ease-smooth);
}
div.stButton > button:hover {
  border-color: var(--accent-teal);
  box-shadow: 0 0 20px var(--accent-teal-glow);
  transform: translateY(-1px);
}
div.stButton > button:active {
  transform: scale(0.97);
}
div.stButton > button[kind="primary"] {
  background: var(--brand-gradient);
  border: none;
  color: #FFFFFF;
}
div.stButton > button[kind="primary"]:hover {
  box-shadow: 0 0 24px var(--accent-purple-glow);
}

/* ---------- Upload dropzone ---------- */
[data-testid="stFileUploaderDropzone"] {
  border: 2px dashed rgba(255,255,255,0.15);
  border-radius: 12px;
  background: var(--bg-surface-1);
  transition: all var(--duration-normal) var(--ease-smooth);
}
[data-testid="stFileUploaderDropzone"]:hover,
[data-testid="stFileUploaderDropzone"]:focus-within {
  border-color: var(--accent-teal);
  background: var(--accent-teal-glow);
  transform: scale(1.01);
}
[data-testid="stFileUploaderDropzone"]:active {
  transform: scale(0.99);
}

/* ---------- Tabs ---------- */
[data-testid="stTabs"] button {
  font-family: var(--font-heading);
  font-weight: 600;
  color: var(--text-secondary);
  border-radius: 10px 10px 0 0;
  transition: color var(--duration-fast) var(--ease-smooth);
}
[data-testid="stTabs"] button:hover {
  color: var(--text-primary);
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--accent-teal);
  background: var(--bg-surface-1);
  border-bottom: 2px solid var(--accent-teal);
}

/* ---------- Expanders / surfaces ---------- */
[data-testid="stExpander"] details {
  background: var(--bg-surface-1);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  transition: border-color var(--duration-fast) var(--ease-smooth);
}
[data-testid="stExpander"] details:hover {
  border-color: rgba(45, 212, 191, 0.35);
}

/* ---------- STATUS-COLORED ALERTS + SUCCESS BOUNCE ---------- */
div.stSuccess, [data-testid="stAlert"].stSuccess {
  border: 1px solid rgba(16, 185, 129, 0.35);
  background: rgba(16, 185, 129, 0.08);
  border-radius: 12px;
  animation: scale-in var(--duration-normal) var(--ease-elastic) both;
}
div.stWarning, [data-testid="stAlert"].stWarning {
  border: 1px solid rgba(249, 115, 22, 0.35);
  background: rgba(249, 115, 22, 0.08);
  border-radius: 12px;
}
div.stError, [data-testid="stAlert"].stError {
  border: 1px solid rgba(239, 68, 68, 0.40);
  background: rgba(239, 68, 68, 0.10);
  border-radius: 12px;
}
div.stInfo, [data-testid="stAlert"].stInfo {
  border: 1px solid rgba(45, 212, 191, 0.30);
  background: rgba(45, 212, 191, 0.06);
  border-radius: 12px;
}

/* ---------- STAGGERED ENTRANCE FOR PAGE BLOCKS ---------- */
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div {
  animation: fade-in-up var(--duration-normal) var(--ease-smooth) both;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(1) { animation-delay: 0ms; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 80ms; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 160ms; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 240ms; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 320ms; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] > div:nth-child(n+6) { animation-delay: 400ms; }

/* ---------- INPUT FOCUS GLOW ---------- */
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus,
textarea:focus {
  border-color: var(--accent-teal) !important;
  box-shadow: 0 0 0 3px var(--accent-teal-glow) !important;
}

/* ---------- Hero & components ---------- */
.hero-heading {
  font-family: var(--font-heading);
  font-weight: 800;
  font-size: clamp(32px, 5vw, 48px);
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 var(--space-4) 0;
}
.hero-sub {
  color: var(--text-secondary);
  font-size: 18px;
}
.feature-card {
  background: var(--bg-surface-1);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: var(--space-6);
  height: 100%;
  transition: transform var(--duration-normal) var(--ease-smooth),
              border-color var(--duration-normal) var(--ease-smooth),
              box-shadow var(--duration-normal) var(--ease-smooth);
}
.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent-teal);
  box-shadow: 0 12px 24px -10px var(--accent-teal-glow);
}
.fc-icon { font-size: 28px; }
.fc-title {
  font-family: var(--font-heading);
  font-weight: 700;
  color: var(--text-primary);
  margin: var(--space-2) 0;
}
.fc-desc { color: var(--text-secondary); font-size: 14px; }

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--bg-surface-2);
  border: 1px solid rgba(16,185,129,0.4);
  color: var(--status-success);
  font-size: 13px;
  font-weight: 600;
}
.status-chip .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-success);
  box-shadow: 0 0 8px var(--status-success);
  animation: glow-pulse 2s infinite;
}

/* ---------- Motion / keyframes ---------- */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fade-in-down {
  from { opacity: 0; transform: translateY(-16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes scale-in {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes glow-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}
.anim-fade-up   { animation: fade-in-up var(--duration-normal) var(--ease-smooth) both; }
.anim-fade-down { animation: fade-in-down var(--duration-normal) var(--ease-smooth) both; }
.anim-scale-in  { animation: scale-in var(--duration-normal) var(--ease-elastic) both; }
.logo-breathe {
  animation: glow-pulse 3s ease-in-out infinite;
  filter: drop-shadow(0 0 18px var(--accent-teal-glow));
}

/* ---------- ACCESSIBILITY — reduced motion ---------- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
</style>
"""


# ============================================================
# INJECTORS & COMPONENT HELPERS
# ============================================================

def inject_design_system():
    """Load tokens, fonts, component styles and motion on any page.
    DESIGN_CSS already contains its own <style> wrapper — do NOT remove it."""
    st.markdown(DESIGN_CSS, unsafe_allow_html=True)


def hero_heading(text: str):
    st.markdown(
        f'<h1 class="hero-heading anim-fade-down">{text}</h1>',
        unsafe_allow_html=True,
    )


def hero_sub(text: str):
    st.markdown(
        f'<p class="hero-sub anim-fade-up" style="animation-delay:100ms">{text}</p>',
        unsafe_allow_html=True,
    )


def feature_card(icon: str, title: str, desc: str, index: int = 0):
    delay = 150 + index * 75
    st.markdown(
        f"""
        <div class="feature-card anim-fade-up" style="animation-delay:{delay}ms">
          <div class="fc-icon">{icon}</div>
          <div class="fc-title">{title}</div>
          <div class="fc-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_chip(label: str):
    st.markdown(
        f'<span class="status-chip anim-scale-in" style="animation-delay:350ms">'
        f'<span class="dot"></span>{label}</span>',
        unsafe_allow_html=True,
    )


def inject_logo_watermark(opacity: float = 0.06, size: str = "60vmin"):
    """Faded, centered logo BEHIND all page content."""
    if not HAS_LOGO:
        return

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
    uri = f"data:image/svg+xml;base64,{svg_b64}"

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
