# 📑 Document Intelligence & Question Extraction Engine (Doc-Intel-Extract)

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/database-PostgreSQL%20%7C%20SQLite-336791.svg?logo=postgresql)](https://www.postgresql.org/)
[![Task Broker](https://img.shields.io/badge/queue-Redis%20%26%20Celery-DC382D.svg?logo=redis)](https://redis.io/)
[![OCR Engine](https://img.shields.io/badge/OCR-PyMuPDF%20%2B%20Gemini%20Vision-orange.svg)]()
[![Tests](https://img.shields.io/badge/tests-38%2F38%20passing-brightgreen.svg)]()
[![Deploy on Render](https://img.shields.io/badge/deploy-Render%20Ready-46E3B7.svg?logo=render)](https://render.com/)

An enterprise-grade, asynchronous document intelligence system engineered to ingest examination papers (digital PDFs, smartphone photos, and degraded scans) and transform them into structured, validated question items, mathematical equations, diagram image snippets, and verified answer keys.

Built by **Muskan Uppal** (UID: `12307888`, B.Tech CSE) for **PBNC Private Limited**.

---

## 🎯 Executive Overview: The Problem & Solution

Traditional OCR engines fail when digitizing examination papers due to four fundamental challenges:
1. **Multi-Page Question Breaks**: Questions starting on Page 1 with options continuing on Page 2 get fragmented.
2. **Formula & Notation Destruction**: Math formulas, fractions, and Greek symbols break under naive text splitters.
3. **Disconnected Answer Keys**: Answers printed in grids or appendix sections require manual cross-referencing.
4. **Synchronous Server Bottlenecks**: Large 50-page PDFs block HTTP worker threads, causing client timeouts.

**Doc-Intel-Extract** solves all four challenges through an intelligent, asynchronous, multi-modal pipeline:

```
[ Uploaded PDF / Image ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Module 3: Binary Magic Byte Validation & SHA-256 Hash │
└─────────────────────────┬──────────────────────────────┘
                          │ (Immediate 202 Accepted)
                          ▼
┌────────────────────────────────────────────────────────┐
│  Module 8: Asynchronous Celery & Background Pipeline   │
└─────────────────────────┬──────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ Module 4: Preprocessing   │   │ Module 5: Hybrid Engine   │
│ - 300 DPI Rasterization   │   │ - PyMuPDF Digital (<0.1s) │
│ - Contrast Enhancement    │   │ - Gemini AI Vision (Scans)│
│ - Diagram Bounding Boxes  │   │ - Multi-Page Stitcher     │
└─────────┬─────────────────┘   └─────────┬─────────────────┘
          └───────────────┬───────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│  Module 6: Answer Key Parser & Fuzzy Question Linker   │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│  Module 7: 4-Factor Confidence Scoring (0.00 - 1.00)   │
│  - Score >= 0.80 ──> CONFIDENT                         │
│  - Score <  0.80 ──> NEEDS_REVIEW (Human Queue)        │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│  Module 9: REST API Layer, Swagger UI & Export Endpoints│
└────────────────────────────────────────────────────────┘
```

---

## 🧩 Complete 10-Module Feature Matrix

| Module | Purpose | Key Files | Core Capabilities |
| :--- | :--- | :--- | :--- |
| **Module 1** | **Core Config & Security** | `app/core/` | Typed Pydantic settings, NIST PBKDF2 password hashing, PyJWT tokens, and granular RBAC (`ADMIN`, `REVIEWER`, `USER`). |
| **Module 2** | **Data Models & Persistence** | `app/models/`, `alembic/` | PostgreSQL & SQLite ORM schemas, UUID primary keys, JSONB bounding boxes, multi-page span arrays, and Alembic migrations. |
| **Module 3** | **Storage & Validation** | `app/storage/` | Binary magic bytes check (`%PDF-`, `\x89PNG`, `\xFF\xD8\xFF`), path traversal neutralization, and SHA-256 deduplication. |
| **Module 4** | **Document Preprocessing** | `app/services/preprocessing/` | Digital vs. Scanned heuristic, 300 DPI page rasterization, contrast enhancement, auto-rotation, and diagram crop isolation. |
| **Module 5** | **Extraction & AI Vision** | `app/services/extractor/` | PyMuPDF digital parser, Gemini/OpenAI Vision engine, regex option parser preserving math formulas, and multi-page continuity stitching. |
| **Module 6** | **Answer Key & Fuzzy Linker**| `app/services/answer_key/` | Formatted list & grid answer key parser, fuzzy identifier linking, conflict detection (e.g. key specifies 'E' for A–D options). |
| **Module 7** | **Scoring & Audit Flags** | `app/services/scoring/` | 4-component weighted scoring (stem 35%, options 35%, layout 15%, answer 15%), `CONFIDENT` / `NEEDS_REVIEW` flags, and audit logs. |
| **Module 8** | **Async Queue & Workers** | `app/workers/` | Celery/Redis background task queue with automatic in-process fallback to FastAPI `BackgroundTasks` when Redis is offline. |
| **Module 9** | **REST API & Swagger UI** | `app/api/v1/`, `app/main.py` | OpenAPI REST routes (`/auth`, `/documents`, `/questions`, `/reviews`), pagination, search filters, and static crop serving. |
| **Module 10**| **Demos & Architecture** | `demo_assets/`, `scripts/` | 10 sample test documents, comprehensive master exam PDF, automated demo runner, Postman collection, and C4 architecture diagrams. |

---

## ⚡ Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.14)
- Git

### 2. Clone & Install
```bash
git clone https://github.com/muskanuppal08/Doc-intel-extract.git
cd Doc-intel-extract

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```
*The default `.env` runs out-of-the-box with lightweight SQLite (`USE_SQLITE=True`) and deterministic mock extraction (`OCR_ENGINE=mock`) with zero external dependencies.*

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Launch the Server
```bash
uvicorn app.main:app --reload --port 8000
```
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Verification & Test Suite

### Run All 38 Automated Unit & Integration Tests:
```bash
pytest tests/ -v
```
*Output: **38 passed in ~2.2s*** covering security, database models, file validation, preprocessing, extraction, answer key matching, scoring, and REST endpoints.

### Run All 10 End-to-End Real-World Scenarios:
```bash
python scripts/run_all_demo_scenarios.py
```

---

## 📋 The 10 Demonstration Scenarios

Every requirement has a dedicated test asset in `demo_assets/`:

| Scenario | Challenge Addressed | Test Asset | Verification Result |
| :--- | :--- | :--- | :---: |
| **1. Digital PDF** | Clean computer-generated vector exam paper | `demo_1_digital.pdf` | **PASS** (100% digital extraction) |
| **2. Single-Page Image** | Phone snapshot / scanned image input | `demo_2_image.png` | **PASS** (Normalizer + OCR) |
| **3. Degraded Scan** | Faded ink, low resolution, noise artifacts | `demo_3_scanned_low_quality.pdf` | **PASS** (Flagged for Review) |
| **4. Multi-Question** | Full multi-item examination ingestion | `demo_4_multi_questions.pdf` | **PASS** (Batched itemization) |
| **5. Multi-Page Span** | Question starting on Page 1, continuing on Page 2 | `demo_5_multipage_span.pdf` | **PASS** (Stitched into 1 item) |
| **6. Math / Formulas** | Trigonometry, integrals, LaTeX, and formula options | `demo_6_options_exam.pdf` | **PASS** (Preserves math symbols) |
| **7. Inline Answer Key** | Embedded answer table within the question paper | `demo_7_inline_answer_key.pdf` | **PASS** (Parsed & matched) |
| **8. Review Queue** | Ambiguous question routing to human moderator | `demo_8_uncertain_review.pdf` | **PASS** (Human resolution flow) |
| **9. Structured Export** | Machine-readable JSON and CSV formatting | `demo_9_structured_output.pdf` | **PASS** (Pydantic serialization) |
| **10. Corrupted Upload** | Spoofed script/binary uploaded as a `.pdf` | `demo_10_invalid.sh` | **PASS** (Rejected with HTTP 415/400) |
| **🌟 Master Exam** | Comprehensive paper with all challenges combined | `comprehensive_master_exam.pdf` | **PASS** (Diagrams + Math + Stitched) |

---

## 🖥️ Interactive Swagger UI Walkthrough

Follow these steps directly in your browser at **[http://localhost:8000/docs](http://localhost:8000/docs)**:

1. **Authorize**: Click the green **Authorize 🔓** button at the top right:
   - `username`: `admin@pbnc.internal`
   - `password`: `admin12345`
   - Click **Authorize** $\to$ **Close**.
2. **Upload Examination**: Open `POST /api/v1/documents/upload` $\to$ **Try it out** $\to$ select `demo_assets/comprehensive_master_exam.pdf` $\to$ **Execute**.
   - Immediate response: `202 Accepted` with your `document_id`.
3. **Poll Processing Status**: Open `GET /api/v1/documents/{id}/status` $\to$ paste `document_id` $\to$ **Execute**.
   - Shows `status: "completed"`, `page_count: 2`, and questions extracted.
4. **View Extracted Questions**: Open `GET /api/v1/documents/{id}/questions` $\to$ paste `document_id` $\to$ **Execute**.
   - Shows structured questions with options `A`, `B`, `C`, `D`, confidence scores, and bounding boxes.
5. **Inspect Human Review Queue**: Open `GET /api/v1/review-queue` $\to$ **Execute**.
   - View any flagged questions and resolve them via `POST /api/v1/questions/{id}/resolve`.

---

## 🚀 Live Cloud Deployment on Render

This service is architected to deploy natively on **[Render.com](https://render.com/)**:

### 1. Architecture Components on Render
1. **FastAPI Web Service**: Serves the API and Swagger documentation.
2. **Managed PostgreSQL**: Relational metadata, questions, and audit logs.
3. **Managed Redis**: Message broker for Celery asynchronous processing.
4. **Celery Worker Service**: Dedicated background compute engine.

### 2. Step-by-Step Deployment Guide
1. Push this repository to GitHub (`main` branch).
2. Log in to **[Render Dashboard](https://dashboard.render.com/)**.
3. **Create PostgreSQL Database**:
   - Click **New +** $\to$ **PostgreSQL** $\to$ Name: `doc-intel-db`.
   - Copy the internal database URL.
4. **Create Redis Instance**:
   - Click **New +** $\to$ **Redis** $\to$ Name: `doc-intel-redis`.
   - Copy the internal Redis URL.
5. **Create the FastAPI Web Service**:
   - Click **New +** $\to$ **Web Service** $\to$ connect `Doc-intel-extract`.
   - Runtime: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variables:
     - `DATABASE_URL`: `[Internal PostgreSQL URL]`
     - `REDIS_URL`: `[Internal Redis URL]`
     - `SECRET_KEY`: `[Your 64-character random key]`
     - `OCR_ENGINE`: `hybrid`
     - `AI_PROVIDER`: `gemini` (or `mock` for zero-cost demo)
     - `GEMINI_API_KEY`: `[Your Google Gemini API Key]`
6. **Deploy Worker (Optional for Scale)**:
   - Create a **Background Worker** on Render with start command:
     `celery -A app.workers.celery_app worker --loglevel=info`

---

## 📬 Postman Collection

An importable collection is located at:
👉 **`postman/DocIntel_Postman_Collection.json`**

Pre-configured requests include:
- `POST /auth/token` (JWT Login)
- `GET /auth/me` (Profile check)
- `POST /documents/upload` (Multipart upload)
- `GET /documents/{id}/status` (Polling)
- `GET /documents/{id}/questions` (Filtered queries)
- `GET /review-queue` (Auditing)
- `POST /questions/{id}/resolve` (Human resolution)
- `POST /documents/link` (Exam $\leftrightarrow$ Answer Key cross-linking)

---

## 🗺️ Project Roadmap

- [x] **Module 1**: Core Configuration & Security (JWT, RBAC, Pydantic settings)
- [x] **Module 2**: PostgreSQL Data Models & Alembic Migrations
- [x] **Module 3**: Secure Storage & Binary Magic Byte Validation
- [x] **Module 4**: Document Preprocessing, Deskewing & High-DPI Rasterization
- [x] **Module 5**: Multi-page Question Extraction & AI Vision Engine
- [x] **Module 6**: Answer Key Parsing & Fuzzy Linking
- [x] **Module 7**: Multi-Factor Confidence Scoring & Quality Audit Flags
- [x] **Module 8**: Asynchronous Redis Queue & Background Workers
- [x] **Module 9**: Complete REST API Layer & Swagger UI
- [x] **Module 10**: Postman Collection & 10 End-to-End Demonstration Scenarios

---

## 👤 Author & Organization

* **Author**: Muskan Uppal
* **UID**: `12307888`
* **Program**: B.Tech in Computer Science and Engineering (CSE)
* **Organization**: PBNC Private Limited
* **Repository**: [https://github.com/muskanuppal08/Doc-intel-extract](https://github.com/muskanuppal08/Doc-intel-extract)

