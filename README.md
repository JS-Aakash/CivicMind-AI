# CivicMind AI

> **Every Voice. Understood. Prioritized. Resolved.**

CivicMind AI is an enterprise-grade civic grievance intelligence platform engineered for multilingual and code-mixed public service grievance classification, priority routing, duplicate detection, temporal-spatial incident clustering, voice & visual evidence extraction, and live municipal command center intelligence. Tailored for municipal operations centered around Chennai, Tamil Nadu, India.

---

## 🏛️ Platform Architecture Overview

CivicMind AI integrates 6 specialized modules into a unified civic operations engine:

1. **Module 1 — Foundation & AI Core**: Local Google MuRIL (`google/muril-base-cased`) embedding pipeline, script identification, and FastAPI backend foundation.
2. **Module 2 — Multilingual Grievance Intelligence**: Fine-tuned classification across native scripts (Tamil, Hindi), code-mixed dialects (Tanglish, Hinglish), and Indian English.
3. **Module 2.5 — MuRIL v1.1 Hardening & Calibration**: Temperature scaling, confidence calibration, and model metrics monitoring.
4. **Module 3 — Smart Routing, Context-Aware Priority, SLA & Explainable Decisions**: Multi-factor priority engine, department routing, SLA dispatch timers, and transparent AI explanations.
5. **Module 4 — Geo + Duplicate Detection + Incident Intelligence + Live Civic Map**: Vector-similarity & spatial-temporal duplicate detection, DBSCAN incident clustering, and MapLibre GL live civic map.
6. **Module 5 — Multimodal Intelligence + Voice + Image Evidence**: Local Whisper speech recognition (Tamil/Hindi/Tanglish) and local Ollama Qwen2.5-VL / Qwen3-VL visual evidence extraction.
7. **Module 6 — Command Center & Analytics**: High-density executive command center, real-time alert dispatch desk, SLA performance telemetry, and human-in-the-loop officer overrides.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router) + React 19 + TypeScript
- **Styling**: Vanilla CSS / Custom CivicMind Dark Design Tokens
- **Mapping**: MapLibre GL JS + CARTO Dark GIS vector tiles
- **Analytics & Icons**: Recharts + Lucide Icons

### Backend
- **Framework**: FastAPI (Python 3.12) with async ASGI architecture
- **AI / NLP Models**:
  - **Text & Embeddings**: Google MuRIL (`google/muril-base-cased`), IndicLID
  - **Speech-to-Text**: Faster-Whisper / Whisper local inference
  - **Visual Reasoning**: Ollama Qwen2.5-VL / Qwen3-VL
- **Database (Optional/Production)**: PostgreSQL with PostGIS and pgvector

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Node.js**: v18+ (v20+ recommended)
- **Python**: v3.10+ (v3.12 recommended)
- **Ollama**: (Optional for local vision reasoning) running `qwen3-vl:4b` or `qwen2.5vl:7b`

---

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

#### Download Local MuRIL Model
```bash
python scripts/download_models.py
```

#### Start FastAPI Server
> **Note**: Make sure your terminal is inside the `backend` directory before running:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*(Alternatively, from the project root directory: `python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload`)*

Interactive API Docs: 👉 **`http://localhost:8000/api/docs`**

---

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Command Center UI: 👉 **`http://localhost:3000`**

---

## 🛰️ GIS & Geographic Focus

- **Default Center**: Chennai, Tamil Nadu, India (`13.0827° N, 80.2707° E`)
- **Localities Tracked**: T. Nagar, Anna Nagar, Velachery, Mylapore, Adyar, Kodambakkam, Royapettah, Guindy, Vadapalani, Porur.

---

## 🧪 Testing

Run backend test suites:
```bash
python -m pytest tests/test_module6_command_center.py -v
```

Validate frontend production build:
```bash
cd frontend
npm run build
```
