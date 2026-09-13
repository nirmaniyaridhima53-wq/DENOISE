# pages/1_Study_Dashboard.py
# PAGE 2: Study Dashboard (placeholder — full tools arrive in Step 5)

import streamlit as st
from pathlib import Path

# From pages/ folder, go one level UP to reach assets/
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()

st.set_page_config(
    page_title="Study Dashboard",
    page_icon=str(LOGO_PATH) if HAS_LOGO else "📚",
    layout="wide",
)

with st.sidebar:
    if HAS_LOGO:
        st.image(str(LOGO_PATH), width=160)

st.title("📚 Study Dashboard")
st.info("You are on Page 2. The full PDF study tools will be moved here in Step 5.")

if st.button("⬅ Back to Home", width="stretch"):
    st.switch_page("app.py")
