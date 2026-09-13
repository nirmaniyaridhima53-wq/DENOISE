# pages/1_Study_Dashboard.py
# PAGE 2: Full PDF Study Dashboard

import sys
from pathlib import Path

import streamlit as st
import pymupdf as fitz  # modern PyMuPDF import
import urllib.parse


# ============================================================
# PATH BOOTSTRAP (lets pages/ import root-level packages)
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import ui_theme  # shared theme helpers (logo watermark)


# ============================================================
# AI SERVICE IMPORT
# ============================================================

AI_IMPORT_ERROR = None

try:
    from services.ai_service import (
        get_ai_status,
        generate_topics as ai_generate_topics,
        generate_youtube_links
