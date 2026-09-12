# DENOISE
# PDF Study Copilot

PDF Study Copilot is a Streamlit web app that turns selected PDF pages into an interactive study workspace.

Users can upload a PDF, choose a page range, and then generate:

- Topic maps
- Subtopic breakdowns
- YouTube study suggestions
- Extracted diagrams/images
- Interactive multiple-choice quizzes

The app is designed as a lightweight AI-powered learning tool and can later be expanded into a larger research or study operating system.

---

## Features

### 1. PDF Upload

Users can upload a PDF file directly from the browser.

The app reads the PDF using PyMuPDF and displays the total number of pages.

---

### 2. Page Range Selection

Users can select a range of pages to process.

Example:

```text
Total pages: 48
Selected range: 7 to 19
