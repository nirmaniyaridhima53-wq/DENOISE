## Project Structure

```text
pdf-study-copilot/
│
├── app.py                      # Page 1: "Get Started" landing page
├── ui_theme.py                 # Shared branding (logo watermark)
├── requirements.txt
├── README.md
├── .gitignore
│
├── assets/
│   └── logo.png                # App logo (header, sidebar, favicon, watermark)
│
├── pages/
│   └── 1_Study_Dashboard.py    # Page 2: full PDF study dashboard
│
├── services/
│   ├── __init__.py
│   └── ai_service.py           # Groq AI engine (topics, links, quiz)
│
└── .streamlit/
    ├── config.toml             # Theme + server settings
    └── secrets.toml.example    # Secrets template (real secrets never committed)

Commit → done.

---

## PART D — Where we go after launch (pick your next track)

```text
TRACK 1 (recommended): VISION AI
  → Add GROQ_VISION_MODEL to secrets
  → AI describes extracted diagrams ("explain this figure")
  → AI reads scanned/image-only PDF pages (OCR via vision)

TRACK 2: UX UPGRADES
  → Export topic map as JSON / quiz as PDF
  → Regenerate buttons per tab
  → Progress bars during AI calls

TRACK 3: MORE PAGES
  → "About" page with your logo story + contact
  → Saved study sessions (cloud storage)

TRACK 4: RESEARCH OS INTEGRATION
  → This app becomes the Learning Module of your bigger Research OS vision
