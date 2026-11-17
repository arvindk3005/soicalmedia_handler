from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

OUT = Path(__file__).parent
SECTIONS = [
("Abstract", "PulsePilot AI is a full-stack social media analytics application built for portfolio demonstration. A React and TypeScript dashboard communicates only with a FastAPI REST API. The backend authenticates users, persists posts in SQLite and runs a content-analysis workflow. It works in a deterministic local demo mode and can be switched to a local Ollama model without changing frontend code."),
("Problem Statement", "Social content tools often separate drafting, analysis and post history. A portfolio project should show a secure frontend-to-backend integration, persistent data management and an AI feature that handles failures clearly. PulsePilot AI addresses this with a small but complete application that another developer can run locally."),
("Objectives", "The system provides account registration and sign-in, API-mediated post storage, content analysis, recommendation display, predictable error responses and a documented local setup. It deliberately avoids claiming model accuracy or external social-network publishing."),
("Technology Stack", "Frontend: React, TypeScript and Vite. Backend: Python, FastAPI and Pydantic. Data: SQLite through Python sqlite3. Security: PBKDF2 password hashing and signed, time-limited bearer tokens. AI: deterministic demo analysis by default, with an optional Ollama HTTP adapter. Delivery: Docker Compose and automated pytest API tests."),
("Architecture", "The browser calls the React client, which stores the bearer token locally and calls the FastAPI API. The API validates each request, obtains the authenticated user from the signed token and uses the database or analysis service. SQLite is accessed only by the backend. The provider adapter selects demo analysis or an Ollama request. Secrets and provider URLs remain in backend environment settings."),
("Working Process", "First, a user registers through POST /api/auth/register and receives a signed token. The client sends that token with each protected request. A post draft is sent to POST /api/analysis. In demo mode, the analyzer extracts topic terms, derives a transparent sentiment label, recommends a hook and suggests hashtags. The draft is then stored through POST /api/posts. GET /api/posts returns only the signed-in user’s records. If Ollama is selected, the adapter requests a JSON response from the configured local model and reports a 502 error if it is unavailable."),
("API Endpoints", "GET /api/health verifies service availability. POST /api/auth/register and POST /api/auth/login issue access tokens. GET /api/posts lists the current user’s posts. POST /api/posts stores a post. POST /api/analysis returns analysis for a post draft. FastAPI exposes interactive endpoint documentation at /docs."),
("Project Structure", "backend/app/api contains routing and auth dependencies; core holds configuration and security; db owns SQLite setup; schemas validates request data; services implements analytics and provider integration; tests exercises the full API flow. frontend/src contains the API client, React application and styles. reports contains this documentation. Docker files make the client and API runnable as separate services."),
("Testing and Limitations", "The offline suite covers health, registration, authenticated post storage, analysis and rejection of unauthenticated requests. The demo analyzer is rule-based, not a trained prediction model. Ollama output is only available when a compatible local model is running. This version does not publish to social networks, collect live platform data, perform authorization roles or use production-grade secret management."),
("Conclusion", "PulsePilot AI demonstrates the essential integration path for an AI-enabled product: a responsive frontend, a validated API, authentication, persistence, a replaceable AI provider and honest fallback behavior. The modular layout makes it suitable for ongoing additions such as OAuth, social API ingestion, analytics charts and cloud deployment."),
]
def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)
def make_doc(path, title, subtitle, sections):
    d=Document(); sec=d.sections[0]; sec.top_margin=Inches(.7); sec.bottom_margin=Inches(.7); sec.left_margin=sec.right_margin=Inches(.8)
    normal=d.styles['Normal']; normal.font.name='Aptos'; normal.font.size=Pt(10.5); normal.font.color.rgb=RGBColor(0,0,0)
    for style_name in ['Title', 'Heading 1', 'Heading 2']:
        style=d.styles[style_name]; style.font.name='Aptos'; style.font.color.rgb=RGBColor(0,0,0)
        style._element.rPr.rFonts.set(qn('w:ascii'), 'Aptos')
    title_paragraph=d.add_heading(title,0); title_paragraph.alignment=WD_ALIGN_PARAGRAPH.CENTER
    pPr = title_paragraph._p.get_or_add_pPr()
    for border in pPr.findall(qn('w:pBdr')): pPr.remove(border)
    p=d.add_paragraph(subtitle); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    d.add_paragraph('Team Members: Arvind Khanna (2481115) and Harsh (2481055)').alignment=WD_ALIGN_PARAGRAPH.CENTER
    d.add_paragraph('Submission: November 2026').alignment=WD_ALIGN_PARAGRAPH.CENTER
    for heading, body in sections:
        d.add_heading(heading,1); d.add_paragraph(body)
    d.add_heading('Repository and Run Guide',1); d.add_paragraph('Repository root: socialmedia_resume. Run the API with uvicorn app.main:app --reload from backend after installing requirements. Run npm install and npm run dev from frontend. The exact setup, environment variables and architecture diagram are in README.md and docs/.')
    d.save(path)
make_doc(OUT/'PulsePilot_AI_Project_Report.docx', 'PulsePilot AI Project Report', 'AI Powered Social Media Analytics Dashboard', SECTIONS)
synopsis=[s for s in SECTIONS if s[0] in {'Abstract','Problem Statement','Objectives','Technology Stack','Architecture','Working Process','Testing and Limitations','Conclusion'}]
make_doc(OUT/'PulsePilot_AI_Project_Synopsis.docx', 'PulsePilot AI Project Synopsis', 'Full Stack Social Media Analytics Dashboard', synopsis)
