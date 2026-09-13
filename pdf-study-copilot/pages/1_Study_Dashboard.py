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
    )
    AI_SERVICE_AVAILABLE = True
except Exception as e:
    AI_SERVICE_AVAILABLE = False
    AI_IMPORT_ERROR = str(e)


# ============================================================
# LOGO CONFIGURATION
# ============================================================

LOGO_PATH = ROOT_DIR / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()


st.set_page_config(
    page_title="Study Dashboard — PDF Study Copilot",
    page_icon=str(LOGO_PATH) if HAS_LOGO else "📚",
    layout="wide",
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
        "quiz_questions",
        "quiz_answers",
        "quiz_submitted",
    ]

    for key in keys_to_reset:
        st.session_state[key] = defaults[key]

    clear_answer_keys()

    if "page_range" in st.session_state:
        del st.session_state["page_range"]


init_state()


# ============================================================
# MOCK FUNCTIONS (used when AI is not configured)
# ============================================================

def mock_generate_topics(text):
    if not text.strip():
        return []

    return [
        {
            "topic": "Extracted PDF Content",
            "summary": "This is a mock topic. Configure Groq to generate real AI topics.",
            "subtopics": [
                {
                    "name": "Selected Page Content",
                    "summary": f"The selected pages contain approximately {len(text)} characters of extracted text.",
                    "keywords": ["PDF", "text extraction", "study"],
                },
                {
                    "name": "AI Topic Mapping",
                    "summary": "Real AI topic mapping will appear after API keys are configured.",
                    "keywords": ["AI", "topics", "subtopics"],
                },
            ],
        }
    ]


def mock_generate_youtube_links(text, topics=None):
    links = []

    if topics:
        for topic in topics:
            topic_name = topic.get("topic", "Topic")
            search_query = f"{topic_name} explained simply"

            url = (
                "https://www.youtube.com/results?search_query="
                + urllib.parse.quote(search_query)
            )

            links.append(
                {
                    "topic": topic_name,
                    "title": search_query,
                    "url": url,
                    "reason": "Mock study suggestion. Configure AI for better suggestions.",
                }
            )
    else:
        search_query = "selected PDF topic explained simply"

        url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote(search_query)
        )

        links.append(
            {
                "topic": "General Study Topic",
                "title": search_query,
                "url": url,
                "reason": "Mock study suggestion. Configure AI for better suggestions.",
            }
        )

    return links


def mock_generate_quiz(text, num_questions=5):
    if not text.strip():
        return []

    questions = []

    for i in range(num_questions):
        questions.append(
            {
                "question": f"Sample question {i + 1}: What is one key idea from the selected PDF pages?",
                "options": [
                    "First sample answer",
                    "Second sample answer",
                    "Third sample answer",
                    "Fourth sample answer",
                ],
                "correct_index": 0,
                "explanation": "This is a mock explanation. Configure AI to generate real quiz questions.",
            }
        )

    return questions


# ============================================================
# AI STATUS HELPER
# ============================================================

def is_ai_ready():
    if not AI_SERVICE_AVAILABLE:
        return False

    try:
        status = get_ai_status()
        return bool(status.get("configured", False))
    except Exception:
        return False


# ============================================================
# AI ACTION FUNCTIONS
# ============================================================

def generate_topics_action():
    text = st.session_state.get("extracted_text", "")

    if not text.strip():
        st.warning("No extracted text found. Extract pages first.")
        return

    if is_ai_ready():
        with st.spinner("Generating topics with AI..."):
            topics = ai_generate_topics(text)

        st.session_state["topics"] = topics

        if not topics:
            st.warning("AI returned no topics. Check API key, model, or PDF text.")
    else:
        st.session_state["topics"] = mock_generate_topics(text)
        st.info("Mock mode: configure Groq in Streamlit secrets for real AI.")


def generate_links_action():
    text = st.session_state.get("extracted_text", "")
    topics = st.session_state.get("topics", [])

    if not text.strip() and not topics:
        st.warning("Extract pages first before generating study links.")
        return

    if is_ai_ready():
        with st.spinner("Generating study links with AI..."):
            links = ai_generate_youtube_links(text, topics)

        st.session_state["youtube_links"] = links

        if not links:
            st.warning("AI returned no study links. Check API key, model, or PDF text.")
    else:
        st.session_state["youtube_links"] = mock_generate_youtube_links(text, topics)
        st.info("Mock mode: configure Groq in Streamlit secrets for real AI.")


def generate_quiz_action(num_questions):
    text = st.session_state.get("extracted_text", "")

    if not text.strip():
        st.warning("Extract pages first before generating a quiz.")
        return

    clear_answer_keys()

    st.session_state["quiz_answers"] = []
    st.session_state["quiz_submitted"] = False

    if is_ai_ready():
        with st.spinner("Generating quiz with AI..."):
            questions = ai_generate_quiz(text, num_questions)

        st.session_state["quiz_questions"] = questions

        if not questions:
            st.warning("AI returned no quiz questions. Check API key, model, or PDF text.")
    else:
        st.session_state["quiz_questions"] = mock_generate_quiz(text, num_questions)
        st.info("Mock mode: configure Groq in Streamlit secrets for real AI.")


# ============================================================
# PDF HELPER FUNCTIONS
# ============================================================

def extract_selected_text(doc, page_numbers):
    text_parts = []

    for page_number in page_numbers:
        if 0 <= page_number < len(doc):
            page = doc.load_page(page_number)
            page_text = page.get_text()

            text_parts.append(
                f"--- Page {page_number + 1} ---\n{page_text}"
            )

    return "\n\n".join(text_parts)


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

                    images.append(
                        {
                            "page": page_number + 1,
                            "name": f"page_{page_number + 1}_image_{image_index}.png",
                            "bytes": pix.tobytes("png"),
                        }
                    )

                    pix = None

                except Exception:
                    continue

    return images


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    if HAS_LOGO:
        st.image(str(LOGO_PATH), width=160)

    if st.button("⬅ Back to Home", width="stretch"):
        st.switch_page("app.py")

    st.divider()

    st.subheader("AI Status")

    if AI_SERVICE_AVAILABLE:
        status = get_ai_status()

        if status.get("configured"):
            st.success(f"Provider: {status.get('provider')}")
            st.success(f"Model: {status.get('model')}")
        else:
            st.warning("AI not configured. Using mock outputs.")

            if status.get("error"):
                st.caption(status["error"])
    else:
        st.warning("AI service not loaded. Using mock outputs.")

        if AI_IMPORT_ERROR:
            st.caption(AI_IMPORT_ERROR)

    st.divider()

    st.subheader("Current PDF")

    if st.session_state["pdf_name"]:
        st.write(f"**PDF:** {st.session_state['pdf_name']}")
        st.write(f"**Total pages:** {st.session_state['total_pages']}")
        st.write(f"**Selected pages:** {len(st.session_state['selected_pages'])}")
    else:
        st.info("No PDF loaded yet.")

    st.divider()

    if st.button("Reset App", width="stretch"):
        st.session_state.clear()
        st.rerun()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📚 Study Dashboard")

st.write(
    """
    Upload a PDF, select pages, and generate:
    - Topic map
    - YouTube study links
    - Diagrams/images
    - Interactive quiz
    """
)


# ============================================================
# UPLOAD SECTION
# ============================================================

st.subheader("Step 1: Upload PDF")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Select a PDF file from your device."
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

            st.success(
                f"Loaded '{uploaded_file.name}' successfully. "
                f"Total pages: {len(doc)}."
            )

        except Exception as e:
            st.error(f"Unable to read PDF. Error: {e}")


# ============================================================
# PAGE SELECTION + PROCESSING
# ============================================================

if st.session_state["pdf_bytes"] is not None:

    try:
        doc = fitz.open(stream=st.session_state["pdf_bytes"], filetype="pdf")
    except Exception as e:
        st.error(f"Unable to open stored PDF. Error: {e}")
        st.stop()

    total_pages = st.session_state["total_pages"] or len(doc)

    st.divider()

    st.subheader("Step 2: Select Pages")

    if total_pages == 0:
        st.warning("This PDF appears to have no pages.")
    else:
        default_end = min(10, total_pages)

        start_page, end_page = st.slider(
            "Select page range",
            min_value=1,
            max_value=total_pages,
            value=(1, default_end),
            key="page_range"
        )

        selected_pages = list(range(start_page - 1, end_page))

        st.caption(
            f"Selected range: page {start_page} to page {end_page}. "
            f"Total selected pages: {len(selected_pages)}."
        )

        st.divider()

        st.subheader("Step 3: Extract Selected Pages")

        if st.button("Extract Selected Pages", type="primary"):
            st.session_state["selected_pages"] = selected_pages

            with st.spinner("Extracting text and images from selected pages..."):
                extracted_text = extract_selected_text(doc, selected_pages)

                if not extracted_text.strip():
                    st.warning(
                        "No extractable text found on the selected pages. "
                        "This PDF may be scanned or image-based."
                    )

                st.session_state["extracted_text"] = extracted_text
                st.session_state["images"] = extract_images_from_pages(
                    doc,
                    selected_pages
                )

                st.session_state["topics"] = []
                st.session_state["youtube_links"] = []
                st.session_state["quiz_questions"] = []
                st.session_state["quiz_answers"] = []
                st.session_state["quiz_submitted"] = False

                clear_answer_keys()

            st.success(
                "Selected pages processed. "
                "Now use each dashboard tab to generate AI outputs."
            )

        if st.session_state["extracted_text"]:
            with st.expander("View extracted text preview", expanded=False):
                st.text(st.session_state["extracted_text"][:2000])

            st.divider()

            # ============================================================
            # STUDY DASHBOARD TABS
            # ============================================================

            st.subheader("Step 4: Study Dashboard")

            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "🧠 Topic Map",
                    "🎥 URL Study",
                    "🖼️ Diagrams",
                    "📝 Quiz",
                ]
            )

            # --------------------------------------------------------
            # TAB 1: TOPIC MAP
            # --------------------------------------------------------

            with tab1:
                st.header("Topic Map")

                if st.button(
                    "Generate Topics",
                    type="primary",
                    width="stretch"
                ):
                    generate_topics_action()

                st.divider()

                if not st.session_state["topics"]:
                    st.info("Click 'Generate Topics' to analyze the selected pages.")
                else:
                    for topic in st.session_state["topics"]:
                        topic_name = topic.get("topic", "Topic")

                        with st.expander(topic_name, expanded=True):
                            st.write(topic.get("summary", ""))

                            for subtopic in topic.get("subtopics", []):
                                st.markdown(f"#### {subtopic.get('name', '')}")
                                st.write(subtopic.get("summary", ""))

                                keywords = subtopic.get("keywords", [])

                                if keywords:
                                    st.caption("Keywords: " + ", ".join(keywords))

                                st.divider()

            # --------------------------------------------------------
            # TAB 2: URL STUDY
            # --------------------------------------------------------

            with tab2:
                st.header("URL Study")

                if st.button(
                    "Generate Study Links",
                    type="primary",
                    width="stretch"
                ):
                    generate_links_action()

                st.divider()

                if not st.session_state["youtube_links"]:
                    st.info("Click 'Generate Study Links' to create YouTube suggestions.")
                else:
                    for link in st.session_state["youtube_links"]:
                        st.markdown(f"#### {link.get('topic', 'Study Topic')}")
                        st.write(f"**Suggested search:** {link.get('title', '')}")
                        st.write(f"**Reason:** {link.get('reason', '')}")
                        st.markdown(
                            f"[Open YouTube Search]({link.get('url', '#')})"
                        )
                        st.divider()

            # --------------------------------------------------------
            # TAB 3: DIAGRAMS
            # --------------------------------------------------------

            with tab3:
                st.header("Diagrams")

                if st.session_state["selected_pages"]:
                    if st.button(
                        "Re-extract Images",
                        width="stretch"
                    ):
                        with st.spinner("Extracting images..."):
                            st.session_state["images"] = extract_images_from_pages(
                                doc,
                                st.session_state["selected_pages"]
                            )

                    st.divider()

                if not st.session_state["images"]:
                    st.info(
                        "No images found on the selected pages. "
                        "Some PDFs store figures as vector graphics or scanned content."
                    )
                else:
                    st.write(f"Found {len(st.session_state['images'])} image(s).")

                    columns = st.columns(3)

                    for index, image in enumerate(st.session_state["images"]):
                        with columns[index % 3]:
                            st.image(
                                image["bytes"],
                                caption=f"Page {image['page']}",
                                width="stretch"
                            )

            # --------------------------------------------------------
            # TAB 4: QUIZ
            # --------------------------------------------------------

            with tab4:
                st.header("Quiz")

                num_questions = st.number_input(
                    "Number of quiz questions",
                    min_value=3,
                    max_value=20,
                    value=5,
                    step=1
                )

                if st.button(
                    "Generate Quiz",
                    type="primary",
                    width="stretch"
                ):
                    generate_quiz_action(int(num_questions))

                st.divider()

                if st.session_state["quiz_questions"]:
                    for index, question in enumerate(st.session_state["quiz_questions"]):
                        st.markdown(f"### Question {index + 1}")
                        st.write(question.get("question", ""))

                        st.radio(
                            "Choose one answer",
                            options=question.get("options", []),
                            key=f"answer_{index}"
                        )

                        st.divider()

                    if st.button("Submit Quiz", type="primary"):
                        answers = []

                        for index in range(len(st.session_state["quiz_questions"])):
                            answers.append(
                                st.session_state.get(f"answer_{index}")
                            )

                        st.session_state["quiz_answers"] = answers
                        st.session_state["quiz_submitted"] = True

                    if (
                        st.session_state["quiz_submitted"]
                        and st.session_state["quiz_answers"]
                    ):
                        score = 0

                        for index, question in enumerate(
                            st.session_state["quiz_questions"]
                        ):
                            if index >= len(st.session_state["quiz_answers"]):
                                continue

                            user_answer = st.session_state["quiz_answers"][index]
                            options = question.get("options", [])
                            correct_index = question.get("correct_index", 0)

                            if (
                                isinstance(correct_index, int)
                                and 0 <= correct_index < len(options)
                                and user_answer == options[correct_index]
                            ):
                                score += 1

                        total = len(st.session_state["quiz_questions"])

                        st.success(f"Your score: {score}/{total}")

                        st.divider()

                        st.subheader("Explanations")

                        for index, question in enumerate(
                            st.session_state["quiz_questions"]
                        ):
                            if index >= len(st.session_state["quiz_answers"]):
                                continue

                            user_answer = st.session_state["quiz_answers"][index]
                            options = question.get("options", [])
                            correct_index = question.get("correct_index", 0)

                            if (
                                isinstance(correct_index, int)
                                and 0 <= correct_index < len(options)
                            ):
                                correct_answer = options[correct_index]
                            else:
                                correct_answer = "Unknown"

                            if user_answer == correct_answer:
                                st.markdown(f"✅ Question {index + 1}: Correct")
                            else:
                                st.markdown(f"❌ Question {index + 1}: Incorrect")

                            st.write(f"**Correct answer:** {correct_answer}")
                            st.write(f"**Explanation:** {question.get('explanation', '')}")
                            st.divider()

                else:
                    st.info(
                        "Click 'Generate Quiz' after extracting pages."
                    )

else:
    st.info("Upload a PDF to begin.")
