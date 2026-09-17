# pages/1_Study_Dashboard.py
# PAGE 2: Research OS Study Workspace
# - NO slider, NO range logic: user types exactly 2 discrete pages (e.g. 5 and 22)
# - NO text extractor: page images go DIRECTLY to Groq Vision qwen/qwen3.8-27b
# - Works for handwritten notes, scanned & non-text-selectable PDFs

import sys
import base64
from pathlib import Path

import streamlit as st
import pymupdf as fitz  # rendering pages to images only (no text extraction)
import urllib.parse


# ============================================================
# PATH BOOTSTRAP
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import ui_theme  # design system + watermark


# ============================================================
# AI SERVICE IMPORT
# ============================================================

AI_IMPORT_ERROR = None

try:
    from services.ai_service import (
        get_ai_status,
        generate_topics as ai_generate_topics,
        generate_youtube_links as ai_generate_youtube_links,
        generate_quiz as ai_generate_quiz,
        transcribe_page_images as ai_transcribe_pages,
    )
    from services.vision_service import explain_image as ai_explain_image

    AI_SERVICE_AVAILABLE = True
except Exception as e:
    AI_SERVICE_AVAILABLE = False
    AI_IMPORT_ERROR = str(e)


# ============================================================
# GLOBAL LIMITS & MODEL LABEL
# ============================================================

VISION_MODEL_LABEL = "qwen/qwen3.8-27b"


# ============================================================
# LOGO CONFIGURATION
# ============================================================

LOGO_PATH = ROOT_DIR / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()


st.set_page_config(
    page_title="Research OS — Study Workspace",
    page_icon=str(LOGO_PATH) if HAS_LOGO else "🧬",
    layout="wide",
)

ui_theme.inject_design_system()
ui_theme.inject_logo_watermark(opacity=0.08, size="85vmin")


# ============================================================
# LOCAL HELPERS (design chips)
# ============================================================

def _warn_chip(label: str):
    st.markdown(
        f'<span class="status-chip" '
        f'style="border-color:rgba(249,115,22,0.45); color:var(--status-warning);">'
        f'<span class="dot" style="background:var(--status-warning); '
        f'box-shadow:0 0 8px var(--status-warning);"></span>'
        f'{label}</span>',
        unsafe_allow_html=True,
    )


def _logo_mark(size: int = 48):
    if not HAS_LOGO:
        return
    logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    st.markdown(
        f'<div class="logo-breathe">'
        f'<img src="data:image/png;base64,{logo_b64}" width="{size}" alt="logo"/>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# DEFAULT SESSION STATE
# ============================================================

def get_defaults():
    return {
        "pdf_bytes": None,
        "pdf_name": None,
        "total_pages": 0,
        "selected_pages": [],
        "extracted_text": "",
        "topics": [],
        "youtube_links": [],
        "images": [],
        "image_explanations": {},
        "quiz_questions": [],
        "quiz_answers": [],
        "quiz_submitted": False,
    }


def init_state():
    defaults = get_defaults()
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_answer_keys():
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]


def reset_learning_outputs():
    defaults = get_defaults()

    keys_to_reset = [
        "selected_pages",
        "extracted_text",
        "topics",
        "youtube_links",
        "images",
        "image_explanations",
        "quiz_questions",
        "quiz_answers",
        "quiz_submitted",
    ]

    for key in keys_to_reset:
        st.session_state[key] = defaults[key]

    clear_answer_keys()


init_state()


# ============================================================
# MOCK FUNCTIONS (used only when AI is not configured)
# ============================================================

def mock_generate_topics(text):
    if not text.strip():
        return []
    return [{"topic": "Extracted Content", "summary": "Mock topic.", "subtopics": []}]

def mock_generate_youtube_links(text, topics=None):
    return [{"topic": "Mock", "title": "mock search", "url": "#", "reason": "mock"}]

def mock_generate_quiz(text, num_questions=5):
    return [{
        "question": "Mock question?",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "explanation": "Mock explanation."
    }]


# ============================================================
# AI STATUS & ACTION HELPERS
# ============================================================

def is_ai_ready():
    if not AI_SERVICE_AVAILABLE:
        return False
    try:
        return bool(get_ai_status().get("configured", False))
    except Exception:
        return False

def generate_topics_action():
    text = st.session_state.get("extracted_text", "")
    if not text.strip():
        st.warning("No extracted text found. Analyze pages first.")
        return
    if is_ai_ready():
        with st.spinner("Generating topics with AI..."):
            st.session_state["topics"] = ai_generate_topics(text)
    else:
        st.session_state["topics"] = mock_generate_topics(text)

def generate_links_action():
    text = st.session_state.get("extracted_text", "")
    topics = st.session_state.get("topics", [])
    if not text.strip() and not topics:
        st.warning("Analyze pages first.")
        return
    if is_ai_ready():
        with st.spinner("Generating study links..."):
            st.session_state["youtube_links"] = ai_generate_youtube_links(text, topics)
    else:
        st.session_state["youtube_links"] = mock_generate_youtube_links(text, topics)

def generate_quiz_action(num_questions):
    text = st.session_state.get("extracted_text", "")
    if not text.strip():
        st.warning("Analyze pages first.")
        return
    clear_answer_keys()
    st.session_state["quiz_answers"] = []
    st.session_state["quiz_submitted"] = False
    if is_ai_ready():
        with st.spinner("Generating quiz..."):
            st.session_state["quiz_questions"] = ai_generate_quiz(text, num_questions)
    else:
        st.session_state["quiz_questions"] = mock_generate_quiz(text, num_questions)


# ============================================================
# PDF HELPER FUNCTIONS
# ============================================================

def render_page_png(doc, page_number: int, dpi: int = 150) -> bytes:
    """Render one PDF page (1-based) to PNG bytes for the vision model."""
    page = doc.load_page(page_number - 1)
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")

def extract_images_from_pages(doc, page_numbers):
    images = []
    for page_number in page_numbers:
        if 0 <= page_number < len(doc):
            page = doc.load_page(page_number)
            image_list = page.get_images(full=True)
            for image_index, image in enumerate(image_list, start=1):
                xref = image[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha > 3:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    images.append({
                        "page": page_number + 1,
                        "name": f"page_{page_number + 1}_image_{image_index}.png",
                        "bytes": pix.tobytes("png"),
                    })
                    pix = None
                except Exception:
                    continue
    return images

def render_diagram_explanation(result, page_number):
    st.caption(f"📖 {result['explanation']}")
    if result.get("quote"):
        st.caption(f"“{result['quote']}”")
    st.caption(f"Source: {result['figure_label']}, Page {page_number}")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    if HAS_LOGO:
        st.image(str(LOGO_PATH), width=200)

    if st.button("⬅ Back to Home", width="stretch"):
        st.switch_page("app.py")

    st.divider()
    st.caption("AI STATUS")

    if AI_SERVICE_AVAILABLE:
        status = get_ai_status()
        if status.get("configured"):
            ui_theme.status_chip("AI Engine Active")
            st.caption(f"Vision model: `{VISION_MODEL_LABEL}`")
        else:
            _warn_chip("Mock Mode")
    else:
        _warn_chip("AI Offline")

    st.divider()
    st.caption("CURRENT PDF")
    if st.session_state["pdf_name"]:
        st.write(f"**{st.session_state['pdf_name']}**")
        st.caption(f"{st.session_state['total_pages']} pages")
    else:
        st.caption("No document loaded.")

    st.divider()
    if st.button("Reset App", width="stretch"):
        st.session_state.clear()
        st.rerun()


# ============================================================
# WORKSPACE HEADER
# ============================================================

h_col1, h_col2, h_col3 = st.columns([1, 6, 2])
with h_col1:
    _logo_mark(48)
with h_col2:
    st.markdown(
        '<h3 style="margin:0; font-family:var(--font-heading); font-weight:700;">'
        'Study <span style="color:var(--accent-teal)">Workspace</span></h3>',
        unsafe_allow_html=True,
    )
with h_col3:
    if is_ai_ready():
        ui_theme.status_chip("Vision Ready")
    else:
        _warn_chip("Mock Mode")

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# PARSING OS PANEL (Upload + Discrete Page Select + Vision Analyze)
# ============================================================

with st.container(border=True):
    st.markdown("#### 📂 Upload & Parsing OS")

    uploaded_file = st.file_uploader(
        "Drag & drop or click to browse",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        if st.session_state["pdf_name"] != uploaded_file.name:
            try:
                pdf_bytes = uploaded_file.getvalue()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_name"] = uploaded_file.name
                st.session_state["total_pages"] = len(doc)

                reset_learning_outputs()
                
                # Clear page inputs so they reset to defaults for the new PDF
                st.session_state.pop("page_1", None)
                st.session_state.pop("page_2", None)

                st.success(f"**{uploaded_file.name}** loaded ({len(doc)} pages).")

            except Exception as e:
                st.error(f"Unable to read PDF. Error: {e}")

    # --------------------------------------------------------
    # PAGE INPUT: TWO DISCRETE PAGES (NO RANGE, NO SLIDER)
    # --------------------------------------------------------

    if st.session_state["pdf_bytes"] is not None:

        try:
            doc = fitz.open(stream=st.session_state["pdf_bytes"], filetype="pdf")
        except Exception as e:
            st.error(f"Unable to open stored PDF. Error: {e}")
            st.stop()

        total_pages = st.session_state["total_pages"] or len(doc)

        if total_pages == 0:
            st.warning("This PDF appears to have no pages.")
        else:
            st.divider()
            st.markdown("#### 🎯 Page Selection")

            st.info(
                "📖 Enter the exact page numbers you want to analyze. "
                "You can pick any two pages (e.g., page 5 and page 22, or page 3 and page 222). "
                "Handwritten & scanned pages are fully supported."
            )

            manual_col1, manual_col2 = st.columns(2)

            with manual_col1:
                st.number_input(
                    "First Page",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1,
                    key="page_1"
                )

            default_p2 = min(2, total_pages)
            with manual_col2:
                st.number_input(
                    "Second Page",
                    min_value=1,
                    max_value=total_pages,
                    value=default_p2,
                    step=1,
                    key="page_2"
                )

            # Get the actual page numbers (1-based)
            p1 = int(st.session_state.page_1)
            p2 = int(st.session_state.page_2)
            
            # Convert to 0-based indices, keep unique and sorted
            selected_pages_zero_based = sorted(list(set([p1 - 1, p2 - 1])))
            
            # For display (1-based)
            display_pages = [p + 1 for p in selected_pages_zero_based]

            st.caption(
                f"Selected: page(s) {', '.join(map(str, display_pages))} • "
                f"sent as images to Groq Vision ({VISION_MODEL_LABEL})"
            )

            # ----------------------------------------------------
            # VISION ANALYSIS: pages -> images -> Groq Vision AI
            # ----------------------------------------------------

            if st.button("⚡ Analyze Pages with Vision AI", type="primary", width="stretch"):
                st.session_state["selected_pages"] = selected_pages_zero_based

                with st.spinner(
                    f"Sending pages as images to Groq Vision ({VISION_MODEL_LABEL})..."
                ):
                    page_pngs = []
                    page_nums = []

                    for zero_based in selected_pages_zero_based:
                        page_pngs.append(render_page_png(doc, zero_based + 1))
                        page_nums.append(zero_based + 1)

                    if is_ai_ready():
                        text, error = ai_transcribe_pages(page_pngs, page_nums)
                    else:
                        text, error = "", "AI not configured (mock mode)."

                    st.session_state["extracted_text"] = text
                    st.session_state["images"] = extract_images_from_pages(
                        doc,
                        selected_pages_zero_based
                    )

                    st.session_state["topics"] = []
                    st.session_state["youtube_links"] = []
                    st.session_state["image_explanations"] = {}
                    st.session_state["quiz_questions"] = []
                    st.session_state["quiz_answers"] = []
                    st.session_state["quiz_submitted"] = False

                    clear_answer_keys()

                if error:
                    st.error(f"Vision analysis failed: {error}")
                else:
                    st.success(
                        "Pages read directly by Groq Vision AI. "
                        "Use the workspace tabs below to generate AI outputs."
                    )

                    for page_num in page_nums:
                        st.caption(
                            f"👁️ Page {page_num}: image sent directly to "
                            f"{VISION_MODEL_LABEL} → converted to typed text."
                        )

            if st.session_state["extracted_text"]:
                with st.expander("View AI-transcribed text preview", expanded=False):
                    st.text(st.session_state["extracted_text"][:2000])


# ============================================================
# STUDY WORKSPACE TABS
# ============================================================

if st.session_state["extracted_text"]:

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🧪 Analysis Modules")

    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Topic Map", "🎥 URL Study", "🖼️ Diagrams", "📝 Quiz"])

    with tab1:
        if st.button("Generate Topics", type="primary", width="stretch"):
            generate_topics_action()
        st.divider()
        if not st.session_state["topics"]:
            st.info("Click 'Generate Topics' to analyze the selected pages.")
        else:
            for topic in st.session_state["topics"]:
                with st.expander(topic.get("topic", "Topic"), expanded=True):
                    st.write(topic.get("summary", ""))
                    for sub in topic.get("subtopics", []):
                        st.markdown(f"#### {sub.get('name', '')}")
                        st.write(sub.get("summary", ""))
                        if sub.get("keywords"):
                            st.caption("Keywords: " + ", ".join(sub["keywords"]))
                        st.divider()

    with tab2:
        if st.button("Generate Study Links", type="primary", width="stretch"):
            generate_links_action()
        st.divider()
        if not st.session_state["youtube_links"]:
            st.info("Click 'Generate Study Links'.")
        else:
            for link in st.session_state["youtube_links"]:
                with st.container(border=True):
                    st.markdown(f"##### {link.get('topic', 'Topic')}")
                    st.caption(f"**Search:** {link.get('title', '')}")
                    st.markdown(f"[Open YouTube Search →]({link.get('url', '#')})")

    with tab3:
        if st.session_state["selected_pages"]:
            if st.button("Re-extract Images", width="stretch"):
                with st.spinner("Extracting images..."):
                    st.session_state["images"] = extract_images_from_pages(doc, st.session_state["selected_pages"])
                    st.session_state["image_explanations"] = {}
            st.divider()

        if not st.session_state["images"]:
            st.info("No embedded images found. The full pages were still read by Vision AI.")
        else:
            for index, image in enumerate(st.session_state["images"]):
                page_number = image["page"]
                cache_key = f"page{page_number}_img{index}"
                cached = st.session_state["image_explanations"].get(cache_key)

                with st.container(border=True):
                    st.image(image["bytes"], width=420)
                    label = cached["figure_label"] if cached else f"Image {index + 1}"
                    st.caption(f"*{label} from Page {page_number}*")

                    if cached:
                        render_diagram_explanation(cached, page_number)
                    else:
                        if st.button("🔍 Click to reveal explanation", key=f"explain_btn_{index}"):
                            with st.spinner("Analyzing diagram visually..."):
                                result = ai_explain_image(image["bytes"], "", page_number, index + 1)
                            if result.get("error"):
                                st.warning(f"Could not explain: {result['error']}")
                            else:
                                st.session_state["image_explanations"][cache_key] = result
                                render_diagram_explanation(result, page_number)

    with tab4:
        num_q = st.number_input("Number of quiz questions", min_value=3, max_value=20, value=5, step=1)
        if st.button("Generate Quiz", type="primary", width="stretch"):
            generate_quiz_action(int(num_q))
        st.divider()

        if st.session_state["quiz_questions"]:
            for index, q in enumerate(st.session_state["quiz_questions"]):
                with st.container(border=True):
                    st.markdown(f"##### Question {index + 1}")
                    st.write(q.get("question", ""))
                    st.radio("Choose one", options=q.get("options", []), key=f"answer_{index}")

            if st.button("Submit Quiz", type="primary", width="stretch"):
                st.session_state["quiz_answers"] = [st.session_state.get(f"answer_{i}") for i in range(len(st.session_state["quiz_questions"]))]
                st.session_state["quiz_submitted"] = True

            if st.session_state["quiz_submitted"] and st.session_state["quiz_answers"]:
                score = sum(1 for i, q in enumerate(st.session_state["quiz_questions"]) if i < len(st.session_state["quiz_answers"]) and st.session_state["quiz_answers"][i] == q.get("options", [])[q.get("correct_index", 0)])
                st.success(f"Your score: {score}/{len(st.session_state['quiz_questions'])}")
                
                st.divider()
                st.subheader("Explanations")
                for i, q in enumerate(st.session_state["quiz_questions"]):
                    if i >= len(st.session_state["quiz_answers"]): continue
                    user_ans = st.session_state["quiz_answers"][i]
                    opts = q.get("options", [])
                    correct_idx = q.get("correct_index", 0)
                    correct_ans = opts[correct_idx] if 0 <= correct_idx < len(opts) else "Unknown"
                    
                    st.markdown(f"{'✅' if user_ans == correct_ans else '❌'} **Question {i + 1}**")
                    st.write(f"**Correct answer:** {correct_ans}")
                    st.write(f"**Explanation:** {q.get('explanation', '')}")
                    st.divider()
