# app.py
# PAGE 1: "Get Started" landing page

import streamlit as st
from pathlib import Path

# Logo lives at: pdf-study-copilot/assets/logo.png
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()

st.set_page_config(
    page_title="PDF Study Copilot — Get Started",
    page_icon=str(LOGO_PATH) if HAS_LOGO else "📚",
    layout="wide",
)

# ============================================================
# HERO SECTION (centered logo + enter button)
# ============================================================

col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    if HAS_LOGO:
        st.image(str(LOGO_PATH), width=320)

    st.title("PDF Study Copilot")
    st.subheader("Turn any PDF into an interactive study session.")
    st.caption("Topic maps • YouTube study links • Diagrams • AI quizzes")

    st.write("")

    if st.button("🚀 Get Started", type="primary", width="stretch"):
        st.switch_page("pages/1_Study_Dashboard.py")

# ============================================================
# FEATURE PREVIEW
# ============================================================

st.divider()

f1, f2, f3, f4 = st.columns(4)

f1.markdown("#### 🧠 Topic Map")
f1.caption("AI extracts topics & subtopics from your selected pages.")

f2.markdown("#### 🎥 URL Study")
f2.caption("Smart YouTube search suggestions for every topic.")

f3.markdown("#### 🖼️ Diagrams")
f3.caption("Automatic extraction of figures & images.")

f4.markdown("#### 📝 Quiz")
f4.caption("Interactive AI-generated quizzes with scoring.")

st.divider()
st.caption("Powered by Streamlit + Groq AI")
