# Document Intelligence & Question Extraction Service (Doc-Intel-Extract)

A scalable, asynchronous document processing service that ingests examination papers and question material (PDFs, multi-page scans, images) and converts them into structured, machine-readable questions and answer keys.

---

## Current Status: Modules 1 & 2 (Core Config, Security & Data Models / Persistence)

This release implements **Module 1** and **Module 2**: the central configuration, security foundations, relational database models, Alembic migrations, and persistence layer required for enterprise document isolation and question extraction.

### Features in Module 1 (Core Configuration & Security):
- **Typed Environment Configuration (`app/core/config.py`)**:
  - Powered by `pydantic-settings` to parse environment variables and `.env` files.
  - Dual-database support: Production PostgreSQL with automatic SQLite fallback for lightweight development.
  - Asynchronous task broker configuration (Redis/Celery).
  - Storage path and upload size limits (50MB maximum).
  - Pluggable OCR/Vision settings (Gemini, OpenAI Vision, or local/mock engines).
- **Cryptographic Security (`app/core/security.py`)**:
  - NIST/OWASP-compliant PBKDF2-HMAC-SHA256 password hashing with unique random salts (600,000 iterations).
  - Signed JSON Web Tokens (PyJWT) with expiration, subject IDs, and role claims.
- **FastAPI Authentication & RBAC (`app/core/auth.py`)**:
  - `OAuth2PasswordBearer` security scheme.
  - Role-Based Access Control (`ADMIN`, `REVIEWER`, `USER`) dependency factories enforcing granular authorization.

### Features in Module 2 (Data Models & Persistence):
- **Comprehensive Relational Schema (`app/models/`)**:
  - **`User`**: Multi-tenant user management with hashed credentials and roles.
  - **`Document`**: Document tracking (file name, path, SHA-256 hash, MIME type, page count, processing status).
  - **`Question`**: Extracted questions with question number, stem text, type (MCQ, Multi-select, Numerical, Descriptive), confidence score, source pages array, and bounding boxes.
  - **`QuestionOption`**: Extracted MCQ choices (`A`, `B`, `C`, `D`, etc.) linked to parent question with visual coordinates.
  - **`AnswerKey`**: Verified or extracted answer keys with normalization and explanations.
  - **`ExtractionWarning`**: Quality audit flags (`LOW_CONFIDENCE`, `BLURRED_REGION`, `MISSING_OPTIONS`, etc.) with severities (`INFO`, `WARNING`, `CRITICAL`).
  - **`DocumentRelationship`**: Cross-document linking (e.g. associating Question Paper documents with separate Answer Key documents).
- **Alembic Database Migrations (`alembic/`)**:
  - Auto-configured environment supporting both PostgreSQL and SQLite.
  - Migration script: `ecb65454b9f3_initial_schema.py`.
- **Validation Schemas (`app/schemas/`)**:
  - Strict Pydantic v2 schemas for all entities supporting API serialization and input validation.

---

## Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.14)
- Git

### 2. Installation
```bash
# Clone repository
git clone https://github.com/muskanuppal08/Doc-intel-extract.git
cd Doc-intel-extract

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```
Default `.env` configuration runs with lightweight SQLite enabled (`USE_SQLITE=True`) so you can run the service without external database servers.

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Run Automated Tests
```bash
pytest tests/unit/test_security.py tests/unit/test_models.py -v
```

### 6. Run Module 1 & 2 Verification Script
```bash
python scripts/verify_modules_1_2.py
```

---

## Project Roadmap

- [x] **Module 1**: Core Configuration & Security (JWT, RBAC, Pydantic settings)
- [x] **Module 2**: PostgreSQL Data Models & Alembic Migrations
- [ ] **Module 3**: Secure Storage & Binary Magic Byte Validation
- [ ] **Module 4**: Document Preprocessing, Deskewing & High-DPI Rasterization
- [ ] **Module 5**: Multi-page Question Extraction & AI Vision Engine
- [ ] **Module 6**: Answer Key Parsing & Fuzzy Linking
- [ ] **Module 7**: Multi-Factor Confidence Scoring & Quality Audit Flags
- [ ] **Module 8**: Asynchronous Redis Queue & Background Workers
- [ ] **Module 9**: Complete REST API Layer & Swagger UI
- [ ] **Module 10**: Postman Collection & 10 End-to-End Demonstration Scenarios
