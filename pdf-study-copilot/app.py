# app.py
# PAGE 1: Research OS Landing & Upload Command Center

import streamlit as st
from pathlib import Path
import pymupdf as fitz  # Needed to validate PDF and count pages immediately

import ui_theme  # Research OS design system

# Logo lives at: pdf-study-copilot/assets/logo.png
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"
HAS_LOGO = LOGO_PATH.exists()

st.set_page_config(
    page_title="Research OS — Command Center",
    page_icon=str(LOGO_PATH) if HAS_LOGO else "🧬",
    layout="wide",
)

# Activate Design System + Background Watermark
ui_theme.inject_design_system()

# Boosted opacity (0.10) and size (90vmin) so it's clearly visible on large PC screens
ui_theme.inject_logo_watermark(opacity=0.10, size="90vmin")

# ============================================================
# HEADER: Navigation & Status
# ============================================================
h_col1, h_col2, h_col3 = st.columns([1, 6, 2])

with h_col1:
    if HAS_LOGO:
        # Logo with "breathing" animation class
        st.markdown(
            f'<div class="logo-breathe" style="width:60px;">'
            f'<img src="data:image/png;base64,{ui_theme.base64.b64encode(open(LOGO_PATH, "rb").read()).decode()}" width="100%"/>'
            f'</div>',
            unsafe_allow_html=True
        )

with h_col2:
    st.markdown(
        '<h3 style="margin:0; font-family:var(--font-heading); font-weight:700; letter-spacing:-0.5px;">'
        'Research <span style="color:var(--accent-teal)">OS</span></h3>',
        unsafe_allow_html=True
    )

with h_col3:
    # Status Chip (Top Right)
    ui_theme.status_chip("AI Engine Active")


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# MAIN LAYOUT: 60% Features / 40% Upload Action
# ============================================================
col_left, col_right = st.columns([3, 2])

# ---------------------------------------------------------
# LEFT COLUMN: Hero & Feature Matrix
# ---------------------------------------------------------
with col_left:
    # Hero Section
     ui_theme.hero_heading("Discover what researchers haven't tested yet")
    ui_theme.hero_sub("Upload papers. Find gaps. Run experiments.")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Interactive Feature Matrix (2x2 Grid)
    # Note: We use index to stagger animation delays (0ms, 75ms, 150ms, 225ms)
    
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        ui_theme.feature_card(
            icon="🧠", 
            title="Topic Map", 
            desc="Interactive knowledge graph extraction from dense literature.",
            index=0
        )
    with row1_col2:
        ui_theme.feature_card(
            icon="🧬", 
            title="Visual AI Engine", 
            desc="Molecular diagram analysis & context-aware explanations.",
            index=1
        )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        ui_theme.feature_card(
            icon="🔍", 
            title="Hypothesis Gaps", 
            desc="Identify missing links and untested variables in current research.",
            index=2
        )
    with row2_col2:
        ui_theme.feature_card(
            icon="📝", 
            title="Synthesis Quiz", 
            desc="Auto-generated comprehension testing & active recall.",
            index=3
        )


# ---------------------------------------------------------
# RIGHT COLUMN: Upload & Parsing OS
# ---------------------------------------------------------
with col_right:
    # Container to style the upload zone area
    st.markdown(
        """
        <div style="background:var(--bg-surface-1); border:1px solid rgba(255,255,255,0.05); 
                    border-radius:16px; padding:2rem; height:100%;">
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("#### 📂 Upload & Parsing OS")
    st.caption("Securely process PDF documents up to 50MB.")
    
    # The Dropzone
    uploaded_file = st.file_uploader(
        "Drag & drop or click to browse",
        type=["pdf"],
        label_visibility="collapsed"
    )

    # State Machine Logic
    if uploaded_file is not None:
        # STATE: Processing / Success
        try:
            pdf_bytes = uploaded_file.getvalue()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)
            
            # Save to session state so Dashboard can access it
            st.session_state["pdf_bytes"] = pdf_bytes
            st.session_state["pdf_name"] = uploaded_file.name
            st.session_state["total_pages"] = total_pages
            
            # Success Indicator
            st.success(f"**{uploaded_file.name}** loaded successfully ({total_pages} pages).")
            
            # CTA
            if st.button("Enter Workspace →", type="primary", width="stretch"):
                # Reset specific dashboard states if needed, but keep PDF data
                st.switch_page("pages/1_Study_Dashboard.py")
                
        except Exception as e:
            st.error(f"Invalid file: {e}")
            
    else:
        # STATE: Idle
        st.info("Waiting for document input...")
        st.markdown(
            """
            <div style="text-align:center; color:var(--text-muted); margin-top:2rem;">
                <div style="font-size:3rem; opacity:0.3;">📄</div>
                <p>No document loaded</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True) # Close container


# ============================================================
# FOOTER
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Powered by Streamlit • Groq AI • Research OS Design System")
