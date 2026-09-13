# services/vision_service.py
# Direct visual analysis of diagrams/images using a Groq vision model.
# NO OCR / text-extraction middle step: the raw image bytes are sent
# straight to the vision model as base64 visual input.

import base64
from typing import Any, Dict

from openai import OpenAI

from services.ai_service import get_ai_config, _clean_json_response


def _image_data_uri(image_bytes: bytes) -> str:
    """Convert raw PNG bytes into a base64 data URI for the vision model."""
    return "data:image/png;base64," + base64.b64encode(image_bytes).decode("utf-8")


def explain_image(
    image_bytes: bytes,
    page_text: str,
    page_number: int,
    image_index: int,
) -> Dict[str, Any]:
    """
    Visually analyze one diagram and return a short explanation.

    Returns:
        {
          "figure_label": str,   # e.g. "Figure 2.1" or "Image 3"
          "explanation": str,    # MAX 1-2 sentences (context-based summary)
          "quote": str,          # quote/paraphrase from page text (may be "")
          "error": None or str
        }
    """
    try:
        config = get_ai_config()
    except Exception as e:
        return {
            "figure_label": f"Image {image_index}",
            "explanation": "",
            "quote": "",
            "error": str(e),
        }

    # Vision model falls back to text model if GROQ_VISION_MODEL is not set
    model = config.get("vision_model") or config["model"]

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

    try:
        response = client.chat.completions.create(
            model=model,
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

        figure_label = str(data.get("figure_label", "")).strip() or f"Image {image_index}"
        explanation = str(data.get("explanation", "")).strip()
        quote = str(data.get("quote", "")).strip()

        if not explanation:
            explanation = "The model could not produce an explanation for this diagram."

        return {
            "figure_label": figure_label,
            "explanation": explanation,
            "quote": quote,
            "error": None,
        }

    except Exception as e:
        return {
            "figure_label": f"Image {image_index}",
            "explanation": "",
            "quote": "",
            "error": str(e),
        }
