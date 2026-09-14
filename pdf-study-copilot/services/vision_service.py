# services/vision_service.py
# Diagram explanation engine with automatic fallback:
#   MODE 1 (TRUE VISION): runs ONLY if GROQ_VISION_MODEL is configured
#   MODE 2 (CONTEXT):     explain from page text / figure captions (always works)
# Errors from BOTH modes are preserved and shown to the user.

import base64
import time
from typing import Any, Dict

from openai import OpenAI

from services.ai_service import (
    get_ai_config,
    _clean_json_response,
    chat_json,
    SYSTEM_JSON_ONLY,
)


# ============================================================
# RETRY SETTINGS (for "over capacity" / rate-limit errors)
# ============================================================

MAX_RETRIES = 2
BACKOFF_SECONDS = [2, 4]


def _is_retryable_error(error: Exception) -> bool:
    status = getattr(error, "status_code", None)

    if status in (429, 500, 502, 503, 504):
        return True

    message = str(error).lower()

    return (
        "over capacity" in message
        or "rate limit" in message
        or "try again" in message
        or "back off" in message
    )


def _image_data_uri(image_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(image_bytes).decode("utf-8")


def _normalize_result(data: Dict[str, Any], image_index: int) -> Dict[str, Any]:
    figure_label = str(data.get("figure_label", "")).strip() or f"Image {image_index}"
    explanation = str(data.get("explanation", "")).strip()
    quote = str(data.get("quote", "")).strip()

    return {
        "figure_label": figure_label,
        "explanation": explanation,
        "quote": quote,
        "error": None,
    }


# ============================================================
# MODE 1: TRUE VISION (only when GROQ_VISION_MODEL is set)
# ============================================================

def _try_vision(
    image_bytes: bytes,
    page_text: str,
    page_number: int,
    image_index: int,
) -> Dict[str, Any]:
    try:
        config = get_ai_config()
    except Exception as e:
        return {
            "figure_label": f"Image {image_index}",
            "explanation": "",
            "quote": "",
            "error": str(e),
        }

    vision_model = str(config.get("vision_model", "")).strip()

    # No vision model configured -> skip the call entirely (do NOT
    # send image_url to a text-only model).
    if not vision_model:
        return {
            "figure_label": f"Image {image_index}",
            "explanation": "",
            "quote": "",
            "error": (
                "No vision model configured. "
                "Add GROQ_VISION_MODEL to Streamlit secrets to enable "
                "true visual analysis."
            ),
        }

    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])

    system_prompt = (
        "You are a precise scientific diagram assistant. "
        "You analyze images DIRECTLY using visual input only (no OCR pipeline). "
        "Return only valid JSON. "
        "Do not include markdown, code fences, or explanations outside JSON."
    )

    user_text = f"""
Look at the attached image. It was taken from page {page_number} of a document.

Below is the text of page {page_number}. Use it ONLY to find a matching quote/paraphrase and surrounding context. The image itself must be analyzed visually.

---PAGE TEXT START---
{(page_text or '')[:3000]}
---PAGE TEXT END---

Tasks:
1. Visually analyze what the diagram/image shows.
2. Write an explanation of MAXIMUM 1-2 short sentences that combines:
   - a context-based summary of what the diagram shows, and
   - a short quote or paraphrase from the page text above that describes this diagram (if such text exists).
3. If a figure label (for example "Figure 2.1") is visible inside the image, report it exactly. Otherwise use "Image {image_index}".

Return only valid JSON with this exact structure:

{{
  "figure_label": "Figure X.X or Image {image_index}",
  "explanation": "1-2 sentence explanation",
  "quote": "short quote or paraphrase from the page text, or empty string if none"
}}
"""

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=vision_model,
                temperature=0.2,
                max_tokens=800,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {
                                "type": "image_url",
                                "image_url": {"url": _image_data_uri(image_bytes)},
                            },
                        ],
                    },
                ],
            )

            content = response.choices[0].message.content or ""
            data = _clean_json_response(content)
            result = _normalize_result(data, image_index)

            if result["explanation"]:
                return result

            last_error = Exception("Vision model returned an empty explanation.")
            break

        except Exception as e:
            last_error = e

            if _is_retryable_error(e) and attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_SECONDS[attempt])
                continue

            break

    return {
        "figure_label": f"Image {image_index}",
        "explanation": "",
        "quote": "",
        "error": str(last_error),
    }


# ============================================================
# MODE 2: CONTEXT-BASED EXPLANATION (FIX 1 — real errors surfaced)
# ============================================================

def _explain_from_context(
    page_text: str,
    page_number: int,
    image_index: int,
) -> Dict[str, Any]:
    user_prompt = f"""
You are explaining a diagram/image extracted from page {page_number} of a document.
You CANNOT see the image itself. Use ONLY the page text below.

---PAGE TEXT START---
{(page_text or '')[:4000]}
---PAGE TEXT END---

Tasks:
1. Search the text for a figure caption.
2. Write an explanation of MAXIMUM 1-2 short sentences.
3. Include a short quote or paraphrase from the page text.
4. Use "Image {image_index}" if no figure label is found.

Return only valid JSON:

{{
  "figure_label": "Figure X.X or Image {image_index}",
  "explanation": "1-2 sentence explanation",
  "quote": "short quote or paraphrase, or empty string"
}}
"""

    try:
        data = chat_json(
            system_prompt=SYSTEM_JSON_ONLY,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=600,
        )

        if not data:
            return {
                "figure_label": f"Image {image_index}",
                "explanation": "",
                "quote": "",
                "error": (
                    "Text model returned no JSON response. "
                    "Check the terminal/Streamlit logs for the API error."
                ),
            }

        result = _normalize_result(data, image_index)

        if not result["explanation"]:
            result["explanation"] = (
                "No figure caption or related context found on this page."
            )

        result["explanation"] = (
            "[Context-based] " + result["explanation"]
        )

        return result

    except Exception as e:
        return {
            "figure_label": f"Image {image_index}",
            "explanation": "",
            "quote": "",
            "error": (
                f"Text fallback failed: {type(e).__name__}: {str(e)}"
            ),
        }


# ============================================================
# MAIN ENTRY (FIX 2 — preserve BOTH vision and fallback errors)
# ============================================================

def explain_image(
    image_bytes: bytes,
    page_text: str,
    page_number: int,
    image_index: int,
) -> Dict[str, Any]:
    vision_result = _try_vision(
        image_bytes,
        page_text,
        page_number,
        image_index,
    )

    if (
        not vision_result.get("error")
        and vision_result.get("explanation")
    ):
        return vision_result

    vision_error = vision_result.get("error", "Unknown vision error")

    context_result = _explain_from_context(
        page_text,
        page_number,
        image_index,
    )

    if context_result.get("error"):
        context_result["error"] = (
            f"Vision failed: {vision_error} | "
            f"Context fallback failed: {context_result['error']}"
        )

    return context_result
