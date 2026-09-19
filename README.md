# Document Intelligence & Question Extraction Service (Doc-Intel-Extract)

A scalable, asynchronous document processing service that ingests examination papers and question material (PDFs, multi-page scans, images) and converts them into structured, machine-readable questions and answer keys.

---

## Current Status: Module 1 (Core Configuration & Security)

This release implements **Module 1**: the central configuration and security foundations required for production-grade, multi-tenant document isolation and API protection.

### Features in Module 1:
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

### 4. Run Tests
```bash
pytest tests/unit/test_security.py -v
```

---

## Live Deployment on Render

### Can this project be pushed live on Render?
**Yes, absolutely!** Render is an excellent, cloud-native platform for this service. Render natively provides:
1. **Web Services**: Runs FastAPI using `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. **Managed PostgreSQL**: 1-click managed database instance that auto-injects `DATABASE_URL`.
3. **Managed Redis**: In-memory Redis instance for Celery/async processing jobs.
4. **Background Workers**: Dedicated worker service running `celery -A app.workers.tasks worker`.

### Step-by-Step Render Deployment Guide:

1. **Push your code to GitHub** (`main` branch).
2. **Log in to [Render.com](https://render.com/)** with your GitHub account.
3. **Create a PostgreSQL Database**:
   - Click **New +** $\to$ **PostgreSQL**.
   - Name: `doc-intel-db`.
   - Render will generate an internal database URL.
4. **Create a Redis Instance**:
   - Click **New +** $\to$ **Redis**.
   - Name: `doc-intel-redis`.
5. **Create the FastAPI Web Service**:
   - Click **New +** $\to$ **Web Service**.
   - Select your repository: `muskanuppal08/Doc-intel-extract`.
   - Runtime: **Python 3**.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Under **Environment Variables**, add:
     - `DATABASE_URL`: `[Paste Internal PostgreSQL URL from Step 3]`
     - `REDIS_URL`: `[Paste Internal Redis URL from Step 4]`
     - `SECRET_KEY`: `[Your secure 64-character random key]`
     - `OCR_ENGINE`: `hybrid`
     - `AI_PROVIDER`: `gemini` (or `mock` for zero-cost demo)
     - `GEMINI_API_KEY`: `[Your Google Gemini API Key]`
6. **Click "Create Web Service"**:
   - Render will build your dependencies, start the FastAPI application, and give you a public HTTPS URL (e.g. `https://doc-intel-extract.onrender.com`).
   - You can immediately open `https://doc-intel-extract.onrender.com/docs` to access the interactive Swagger UI!

---

## Project Roadmap

- [x] **Module 1**: Core Configuration & Security (JWT, RBAC, Pydantic settings)
- [ ] **Module 2**: PostgreSQL Data Models & Alembic Migrations
- [ ] **Module 3**: Secure Storage & Binary Magic Byte Validation
- [ ] **Module 4**: Document Preprocessing, Deskewing & High-DPI Rasterization
- [ ] **Module 5**: Multi-page Question Extraction & AI Vision Engine
- [ ] **Module 6**: Answer Key Parsing & Fuzzy Linking
- [ ] **Module 7**: Multi-Factor Confidence Scoring & Quality Audit Flags
- [ ] **Module 8**: Asynchronous Redis Queue & Background Workers
- [ ] **Module 9**: Complete REST API Layer & Swagger UI
- [ ] **Module 10**: Postman Collection & 10 End-to-End Demonstration Scenarios
