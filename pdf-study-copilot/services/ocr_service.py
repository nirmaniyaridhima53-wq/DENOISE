# services/ocr_service.py
# Handwritten / scanned-page OCR engine.
#
# Pipeline:
#   1) Try native PDF text (typed text).
#   2) If the page has (almost) no text -> render page to PNG -> OCR via vision model.
#
# OCR providers (priority order, both OpenAI-compatible -> no extra dependencies):
#   1) Groq vision model   (only if GROQ_VISION_MODEL secret exists)
#   2) Google Gemini       (free key from Google AI Studio -> GEMINI_API_KEY secret)

import base64
import os
from typing import Any, Dict, Optional, Tuple

import streamlit as st
from openai import OpenAI


# Below this character count a page is treated as scanned / handwritten
MIN_NATIVE_TEXT_CHARS = 40

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

OCR_SYSTEM_PROMPT = (
    "You are a precise OCR engine. "
    "Transcribe ALL text visible on the page image, including handwritten notes, "
    "margin annotations, labels and equations. "
    "Preserve line breaks and natural reading order. "
    "Return ONLY the transcribed text. No comments, no markdown, no code fences."
)


# ============================================================
# SECRET HELPER
# ============================================================

def _secret(key: str, default: Any = None) -> Any:
    try:
        value = st.secrets[key]
        if value is not None and str(value).strip() != "":
            return value
    except Exception:
        pass

    return os.getenv(key, default)


# ============================================================
# PROVIDER SELECTION
# ============================================================

def get_ocr_provider() -> Optional[Dict[str, str]]:
    """Return the first available OCR provider config, or None."""
    # 1) Groq vision model (if the user ever configures one)
    try:
        from services.ai_service import get_ai_config

        cfg = get_ai_config()
        vision_model = str(cfg.get("vision_model", "")).strip()

        if vision_model:
            return {
                "name": "groq-vision",
                "api_key": cfg["api_key"],
                "base_url": cfg["base_url"],
                "model": vision_model,
            }
    except Exception:
        pass

    # 2) Google Gemini (free tier, excellent handwriting OCR)
    gemini_key = _secret("GEMINI_API_KEY")

    if gemini_key:
        return {
            "name": "gemini",
            "api_key": str(gemini_key).strip(),
            "base_url": GEMINI_BASE_URL,
            "model": str(_secret("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)).strip(),
        }

    return None


# ============================================================
# IMAGE HELPERS
# ============================================================

def _image_data_uri(png_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")


def render_page_png(doc, page_number: int, dpi: int = 200) -> bytes:
    """Render a PDF page (1-based page number) to PNG bytes."""
    page = doc.load_page(page_number - 1)
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")


def _strip_code_fences(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


# ============================================================
# OCR CALL
# ============================================================

def ocr_page_image(png_bytes: bytes) -> Tuple[str, Optional[str]]:
    """
    Run OCR on one page image.
    Returns: (transcribed_text, error_or_None)
    """
    provider = get_ocr_provider()

    if not provider:
        return "", (
            "No OCR engine configured. Add GEMINI_API_KEY (free from Google AI Studio) "
            "or GROQ_VISION_MODEL to Streamlit secrets to read handwritten/scanned pages."
        )

    try:
        client = OpenAI(
            api_key=provider["api_key"],
            base_url=provider["base_url"],
        )

        response = client.chat.completions.create(
            model=provider["model"],
            temperature=0.0,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": OCR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Transcribe this page exactly as written:",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": _image_data_uri(png_bytes)},
                        },
                    ],
                },
            ],
        )

        text = _strip_code_fences(response.choices[0].message.content or "")

        if not text:
            return "", f"OCR provider '{provider['name']}' returned empty text."

        return text, None

    except Exception as e:
        return "", f"OCR failed ({provider['name']}): {e}"


# ============================================================
# SMART PER-PAGE EXTRACTION (typed + handwritten in one system)
# ============================================================

def extract_page_text(doc, page_number: int) -> Dict[str, Any]:
    """
    Extract one page (1-based):
      - native typed text when present
      - otherwise render + OCR (handwritten / scanned pages)

    Returns:
        {
          "page":  int,
          "text":  str,
          "mode":  "typed" | "ocr" | "empty",
          "error": str or None
        }
    """
    page = doc.load_page(page_number - 1)
    native = (page.get_text() or "").strip()

    # Case 1: normal typed PDF text
    if len(native) >= MIN_NATIVE_TEXT_CHARS:
        return {
            "page": page_number,
            "text": native,
            "mode": "typed",
            "error": None,
        }

    # Case 2: scanned / handwritten -> render and OCR
    png_bytes = render_page_png(doc, page_number)
    text, error = ocr_page_image(png_bytes)

    if text:
        return {
            "page": page_number,
            "text": text,
            "mode": "ocr",
            "error": None,
        }

    # Case 3: OCR unavailable/failed -> keep whatever native fragments exist
    if native:
        return {
            "page": page_number,
            "text": native,
            "mode": "typed",
            "error": error,
        }

    return {
        "page": page_number,
        "text": "",
        "mode": "empty",
        "error": error,
    }
