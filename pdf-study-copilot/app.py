# app.py

import streamlit as st
import fitz  # PyMuPDF
import urllib.parse


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="PDF Study Copilot",
    page_icon="📚",
    layout="wide"
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

    # Reset page range slider widget if it exists
    if "page_range" in st.session_state:
        del st.session_state["page_range"]


init_state()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_selected_text(doc, page_numbers):
    """
    Extract text from selected PDF pages.
    page_numbers should be zero-indexed.
    Example: [0, 1, 2] means pages 1, 2, 3.
    """
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
    """
    Extract embedded images from selected PDF pages.
    """
    images = []

    for page_number in page_numbers:
        if 0 <= page_number < len(doc):
            page = doc.load_page(page_number)
            image_list = page.get_images(full=True)

            for image_index, image in enumerate(image_list, start=1):
                xref = image[0]

                try:
                    pix = fitz.Pixmap(doc, xref)

                    # Convert CMYK to RGB if needed
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


def generate_mock_topics(text):
    """
    Placeholder topic generator.
    This will later be replaced by Grok/Groq AI topic mapping.
    """
    if not text.strip():
        return []

    return [
        {
            "topic": "Extracted PDF Content",
            "summary": "This is a placeholder topic. AI topic mapping will replace this.",
            "subtopics": [
                {
                    "name": "Selected Page Content",
                    "summary": f"The selected pages contain approximately {len(text)} characters of extracted text.",
                    "keywords": ["PDF", "text extraction", "study"],
                },
                {
                    "name": "AI Topic Mapping",
                    "summary": "The next version will send this text to Grok/Groq and return structured topics and subtopics.",
                    "keywords": ["AI", "topics", "subtopics"],
                },
            ],
        }
    ]


def generate_youtube_search_links(topics):
    """
    Placeholder YouTube study link generator.
    This will later be improved by AI.
    """
    links = []

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
                "reason": "Placeholder study suggestion. AI will improve this later.",
            }
        )

    return links


def generate_mock_quiz(text, num_questions):
    """
    Placeholder quiz generator.
    This will later be replaced by Grok/Groq quiz generation.
    """
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
                "explanation": "This is a placeholder explanation. Real AI-generated explanations will appear later.",
            }
        )

    return questions


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("PDF Study Copilot")

    st.caption("MVP Mode: Front-end shell with placeholder AI outputs.")

    st.divider()

    st.subheader("Current Status")

    if st.session_state["pdf_name"]:
        st.write(f"**PDF:** {st.session_state['pdf_name']}")
        st.write(f"**Total pages:** {st.session_state['total_pages']}")
        st.write(f"**Selected pages:** {len(st.session_state['selected_pages'])}")
    else:
        st.info("No PDF loaded yet.")

    st.divider()

    if st.button("Reset App", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ============================================================
# MAIN HEADER
# ============================================================

st.title("📚 PDF Study Copilot")

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
    # Load only when a new file is uploaded
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
# PAGE SELECTION SECTION
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

                # Placeholder AI outputs
                st.session_state["topics"] = generate_mock_topics(extracted_text)
                st.session_state["youtube_links"] = generate_youtube_search_links(
                    st.session_state["topics"]
                )

                # Reset quiz state
                st.session_state["quiz_questions"] = []
                st.session_state["quiz_answers"] = []
                st.session_state["quiz_submitted"] = False

            st.success("Selected pages processed successfully.")

        # Show extracted text preview
        if st.session_state["extracted_text"]:
            with st.expander("View extracted text preview", expanded=False):
                st.text(st.session_state["extracted_text"][:2000])

            st.divider()

            # ============================================================
            # STUDY DASHBOARD
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

                if not st.session_state["topics"]:
                    st.info("No topics generated yet.")
                else:
                    for topic in st.session_state["topics"]:
                        with st.expander(topic["topic"], expanded=True):
                            st.write(topic["summary"])

                            for subtopic in topic["subtopics"]:
                                st.markdown(f"#### {subtopic['name']}")
                                st.write(subtopic["summary"])

                                if subtopic.get("keywords"):
                                    keywords = ", ".join(subtopic["keywords"])
                                    st.caption(f"Keywords: {keywords}")

                                st.divider()

                    st.info(
                        "Placeholder topics shown. "
                        "The next file will connect this to Grok/Groq."
                    )

            # --------------------------------------------------------
            # TAB 2: URL STUDY
            # --------------------------------------------------------

            with tab2:
                st.header("URL Study")

                if not st.session_state["youtube_links"]:
                    st.info("No study links generated yet.")
                else:
                    for link in st.session_state["youtube_links"]:
                        st.markdown(f"#### {link['topic']}")
                        st.write(f"**Suggested search:** {link['title']}")
                        st.write(f"**Reason:** {link['reason']}")
                        st.markdown(
                            f"[Open YouTube Search]({link['url']})"
                        )
                        st.divider()

                    st.info(
                        "Placeholder links shown. "
                        "AI will generate better topic-based study suggestions later."
                    )

            # --------------------------------------------------------
            # TAB 3: DIAGRAMS
            # --------------------------------------------------------

            with tab3:
                st.header("Diagrams")

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
                                use_container_width=True
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

                if st.button("Generate Quiz", type="primary"):
                    st.session_state["quiz_questions"] = generate_mock_quiz(
                        st.session_state["extracted_text"],
                        int(num_questions)
                    )
                    st.session_state["quiz_answers"] = []
                    st.session_state["quiz_submitted"] = False

                if st.session_state["quiz_questions"]:
                    st.divider()

                    for index, question in enumerate(st.session_state["quiz_questions"]):
                        st.markdown(f"### Question {index + 1}")
                        st.write(question["question"])

                        st.radio(
                            "Choose one answer",
                            options=question["options"],
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
                            user_answer = st.session_state["quiz_answers"][index]
                            correct_answer = question["options"][
                                question["correct_index"]
                            ]

                            if user_answer == correct_answer:
                                score += 1

                        total = len(st.session_state["quiz_questions"])

                        st.success(f"Your score: {score}/{total}")

                        st.divider()

                        st.subheader("Explanations")

                        for index, question in enumerate(
                            st.session_state["quiz_questions"]
                        ):
                            user_answer = st.session_state["quiz_answers"][index]
                            correct_answer = question["options"][
                                question["correct_index"]
                            ]

                            if user_answer == correct_answer:
                                st.markdown(f"✅ Question {index + 1}: Correct")
                            else:
                                st.markdown(f"❌ Question {index + 1}: Incorrect")

                            st.write(f"**Correct answer:** {correct_answer}")
                            st.write(f"**Explanation:** {question['explanation']}")
                            st.divider()

                else:
                    st.info(
                        "Click 'Generate Quiz' after extracting pages. "
                        "This is currently using placeholder quiz questions."
                    )

else:
    st.info("Upload a PDF to begin.")
