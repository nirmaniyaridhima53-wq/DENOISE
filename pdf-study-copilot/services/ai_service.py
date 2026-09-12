# services/ai_service.py

import json
import os
import re
import urllib.parse
from typing import Any, Dict, List

import streamlit as st
from openai import OpenAI


# ============================================================
# PROVIDER CONFIGURATION
# ============================================================

SUPPORTED_PROVIDERS = {"xai", "groq"}

PROVIDER_BASE_URLS = {
    "xai": "https://api.x.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
}

DEFAULT_MODELS = {
    "xai": "grok-beta",
    "groq": "llama-3.3-70b-versatile",
}

MAX_CONTEXT_CHARS = 18000

SYSTEM_JSON_ONLY = (
    "You are a precise educational assistant. "
    "Return only valid JSON. "
    "Do not include markdown, code fences, comments, or explanations."
)


# ============================================================
# SECRET HANDLING
# ============================================================

def _secret(key: str, default: Any = None) -> Any:
    """
    Get secret from Streamlit secrets first.
    Fall back to environment variables if needed.
    """
    try:
        value = st.secrets[key]
        if value is not None and str(value).strip() != "":
            return value
    except Exception:
        pass

    return os.getenv(key, default)


def get_ai_config() -> Dict[str, str]:
    """
    Read AI provider configuration from secrets.

    Expected secrets:
        AI_PROVIDER = "xai" or "groq"
        XAI_API_KEY = "..."
        XAI_MODEL = "..."
        GROQ_API_KEY = "..."
        GROQ_MODEL = "..."
    """
    provider = str(_secret("AI_PROVIDER", "xai")).lower().strip()

    if provider not in SUPPORTED_PROVIDERS:
        provider = "xai"

    if provider == "xai":
        api_key = _secret("XAI_API_KEY")
        model = str(_secret("XAI_MODEL", DEFAULT_MODELS["xai"])).strip()
    else:
        api_key = _secret("GROQ_API_KEY")
        model = str(_secret("GROQ_MODEL", DEFAULT_MODELS["groq"])).strip()

    if not api_key or str(api_key).strip() == "":
        raise RuntimeError(
            "Missing AI API key. "
            "Add XAI_API_KEY or GROQ_API_KEY to .streamlit/secrets.toml."
        )

    api_key = str(api_key).strip()

    if "YOUR_" in api_key.upper():
        raise RuntimeError(
            "Please replace the placeholder API key in .streamlit/secrets.toml."
        )

    if not model:
        model = DEFAULT_MODELS[provider]

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": PROVIDER_BASE_URLS[provider],
    }


def get_ai_status() -> Dict[str, Any]:
    """
    Safe status checker for UI display.
    """
    try:
        config = get_ai_config()
        return {
            "configured": True,
            "provider": config["provider"],
            "model": config["model"],
            "error": None,
        }
    except Exception as e:
        return {
            "configured": False,
            "provider": None,
            "model": None,
            "error": str(e),
        }


def _get_client():
    """
    Create OpenAI-compatible client for xAI Grok or Groq.
    """
    config = get_ai_config()

    client = OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )

    return client, config


# ============================================================
# JSON CLEANING
# ============================================================

def _strip_code_fences(text: str) -> str:
    """
    Remove markdown code fences if the model accidentally adds them.
    """
    text = (text or "").strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return text.strip()


def _clean_json_response(text: str) -> Dict[str, Any]:
    """
    Convert AI response into JSON.
    Handles:
        - raw JSON
        - JSON inside code fences
        - JSON embedded in extra text
    """
    text = _strip_code_fences(text)

    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]

            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return {}

        return {}


# ============================================================
# CORE AI CALL
# ============================================================

def chat_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 3500,
) -> Dict[str, Any]:
    """
    Send a chat request and return JSON.
    """
    try:
        client, config = _get_client()

        response = client.chat.completions.create(
            model=config["model"],
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content or ""
        return _clean_json_response(content)

    except Exception as e:
        st.error(f"AI request failed: {e}")
        return {}


# ============================================================
# TEXT HELPERS
# ============================================================

def _truncate_text(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    Prevent extremely large PDF text from exceeding AI context limits.
    """
    text = (text or "").strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "\n\n[Text truncated for AI context limit.]"


# ============================================================
# NORMALIZATION FUNCTIONS
# ============================================================

def _normalize_topics(raw_topics: List[Any]) -> List[Dict[str, Any]]:
    """
    Clean and validate topic JSON from AI.
    """
    clean_topics = []

    for topic in raw_topics:
        if not isinstance(topic, dict):
            continue

        topic_name = str(topic.get("topic", "")).strip()
        topic_summary = str(topic.get("summary", "")).strip()

        if not topic_name:
            continue

        raw_subtopics = topic.get("subtopics", [])
        clean_subtopics = []

        if isinstance(raw_subtopics, list):
            for subtopic in raw_subtopics:
                if not isinstance(subtopic, dict):
                    continue

                subtopic_name = str(subtopic.get("name", "")).strip()
                subtopic_summary = str(subtopic.get("summary", "")).strip()

                if not subtopic_name:
                    continue

                raw_keywords = subtopic.get("keywords", [])

                if isinstance(raw_keywords, str):
                    raw_keywords = [raw_keywords]

                keywords = []

                if isinstance(raw_keywords, list):
                    for keyword in raw_keywords:
                        keyword = str(keyword).strip()
                        if keyword:
                            keywords.append(keyword)

                clean_subtopics.append(
                    {
                        "name": subtopic_name,
                        "summary": subtopic_summary,
                        "keywords": keywords,
                    }
                )

        clean_topics.append(
            {
                "topic": topic_name,
                "summary": topic_summary,
                "subtopics": clean_subtopics,
            }
        )

    return clean_topics


def _youtube_search_url(query: str) -> str:
    """
    Convert a search query into a YouTube search URL.
    """
    query = query.strip()
    return (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(query)
    )


def _normalize_youtube_links(raw_links: List[Any]) -> List[Dict[str, Any]]:
    """
    Clean and validate YouTube suggestion JSON from AI.
    """
    clean_links = []

    for item in raw_links:
        if not isinstance(item, dict):
            continue

        topic = str(item.get("topic", "")).strip()
        search_query = str(item.get("search_query", "")).strip()
        reason = str(item.get("reason", "")).strip()

        if not search_query:
            continue

        url = str(item.get("url", "")).strip()

        if not url:
            url = _youtube_search_url(search_query)

        clean_links.append(
            {
                "topic": topic or "Study Topic",
                "title": search_query,
                "url": url,
                "reason": reason,
            }
        )

    return clean_links


def _normalize_quiz_questions(raw_questions: List[Any]) -> List[Dict[str, Any]]:
    """
    Clean and validate quiz JSON from AI.
    """
    clean_questions = []

    for question in raw_questions:
        if not isinstance(question, dict):
            continue

        question_text = str(question.get("question", "")).strip()
        raw_options = question.get("options", [])
        explanation = str(question.get("explanation", "")).strip()

        if not question_text:
            continue

        if not isinstance(raw_options, list):
            continue

        options = []

        for option in raw_options:
            option = str(option).strip()
            if option:
                options.append(option)

        if len(options) < 2:
            continue

        # Keep maximum 4 options for clean MCQ UI
        options = options[:4]

        try:
            correct_index = int(question.get("correct_index", 0))
        except Exception:
            correct_index = 0

        if correct_index < 0 or correct_index >= len(options):
            correct_index = 0

        clean_questions.append(
            {
                "question": question_text,
                "options": options,
                "correct_index": correct_index,
                "explanation": explanation,
            }
        )

    return clean_questions


# ============================================================
# FEATURE 1: TOPIC MAPPING
# ============================================================

def generate_topics(extracted_text: str) -> List[Dict[str, Any]]:
    """
    Generate structured topics and subtopics from selected PDF text.
    """
    text = _truncate_text(extracted_text)

    if not text:
        return []

    user_prompt = f"""
Analyze the following extracted PDF text and identify all important topics and subtopics.

Return only valid JSON with this exact structure:

{{
  "topics": [
    {{
      "topic": "Main topic name",
      "summary": "Short summary of the main topic",
      "subtopics": [
        {{
          "name": "Subtopic name",
          "summary": "Short summary of the subtopic",
          "keywords": ["keyword1", "keyword2"]
        }}
      ]
    }}
  ]
}}

Rules:
- Use concise educational language.
- Base the topics only on the provided text.
- If the text is unclear, return an empty topics list.
- Do not include markdown.
- Do not include code fences.
- Do not include explanations outside JSON.

Extracted PDF text:

{text}
"""

    result = chat_json(
        system_prompt=SYSTEM_JSON_ONLY,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=3500,
    )

    raw_topics = result.get("topics", [])

    if not isinstance(raw_topics, list):
        return []

    return _normalize_topics(raw_topics)


# ============================================================
# FEATURE 2: YOUTUBE / URL STUDY
# ============================================================

def generate_youtube_links(
    extracted_text: str,
    topics: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate YouTube search suggestions for topics and subtopics.

    Important:
    We do not ask the AI to invent direct YouTube video URLs.
    We ask for search queries, then convert them into safe YouTube search links.
    """
    text = _truncate_text(extracted_text, max_chars=12000)

    topic_context = ""

    if topics:
        topic_lines = []

        for topic in topics:
            topic_name = topic.get("topic", "")

            if topic_name:
                topic_lines.append(f"- {topic_name}")

            for subtopic in topic.get("subtopics", []):
                subtopic_name = subtopic.get("name", "")

                if subtopic_name:
                    topic_lines.append(f"  - {subtopic_name}")

        if topic_lines:
            topic_context = "Known topics and subtopics:\n" + "\n".join(topic_lines)

    if not text and not topic_context:
        return []

    user_prompt = f"""
You are helping a student find useful YouTube learning content.

Based on the extracted PDF text and known topics, suggest useful YouTube search queries.

Do not invent specific video IDs.
Do not invent direct watch URLs.
Only provide search queries that are likely to return useful educational videos.

Return only valid JSON with this exact structure:

{{
  "videos": [
    {{
      "topic": "Topic name",
      "search_query": "youtube search query",
      "reason": "Why this search is useful"
    }}
  ]
}}

Rules:
- Create 1 to 3 search queries per major topic.
- Keep search queries short and natural.
- Base suggestions on the provided text and topics.
- Do not include markdown.
- Do not include code fences.
- Do not include explanations outside JSON.

{topic_context}

Extracted PDF text:

{text}
"""

    result = chat_json(
        system_prompt=SYSTEM_JSON_ONLY,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=2500,
    )

    raw_links = result.get("videos", [])

    if not isinstance(raw_links, list):
        return []

    return _normalize_youtube_links(raw_links)


# ============================================================
# FEATURE 3: QUIZ GENERATION
# ============================================================

def generate_quiz(
    extracted_text: str,
    num_questions: int = 5,
) -> List[Dict[str, Any]]:
    """
    Generate multiple-choice quiz questions from selected PDF text.
    """
    text = _truncate_text(extracted_text)

    if not text:
        return []

    try:
        num_questions = int(num_questions)
    except Exception:
        num_questions = 5

    # Keep quiz generation within safe bounds
    num_questions = max(3, min(20, num_questions))

    user_prompt = f"""
Create {num_questions} multiple-choice questions from the following extracted PDF text.

Return only valid JSON with this exact structure:

{{
  "questions": [
    {{
      "question": "Question text",
      "options": [
        "Option 1",
        "Option 2",
        "Option 3",
        "Option 4"
      ],
      "correct_index": 0,
      "explanation": "Short explanation of the correct answer"
    }}
  ]
}}

Rules:
- Create exactly {num_questions} questions.
- Each question must have 4 options.
- correct_index must be an integer from 0 to 3.
- Questions must be based only on the provided text.
- Make questions educational and clear.
- Do not include markdown.
- Do not include code fences.
- Do not include explanations outside JSON.

Extracted PDF text:

{text}
"""

    result = chat_json(
        system_prompt=SYSTEM_JSON_ONLY,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=4000,
    )

    raw_questions = result.get("questions", [])

    if not isinstance(raw_questions, list):
        return []

    return _normalize_quiz_questions(raw_questions)
