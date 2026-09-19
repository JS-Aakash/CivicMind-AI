# CivicMind AI

<div align="center">

**Enterprise Multimodal Civic Grievance Intelligence & Automated Redressal Platform**

*Every Voice. Understood. Prioritized. Resolved.*

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016%20%2B%20React%2019-black?style=flat&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%28Python%203.12%29-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MuRIL](https://img.shields.io/badge/NLP-Google%20MuRIL%20v1.1-4285F4?style=flat&logo=google)](https://huggingface.co/google/muril-base-cased)
[![Whisper](https://img.shields.io/badge/Speech-OpenAI%20Whisper-00A67E?style=flat&logo=openai)](https://github.com/openai/whisper)
[![Qwen-VL](https://img.shields.io/badge/Vision-Qwen2.5--VL-7928CA?style=flat)](https://github.com/QwenLM/Qwen-VL)
[![PostGIS](https://img.shields.io/badge/Spatial-PostGIS%20%2B%20ST--DBSCAN-336791?style=flat&logo=postgresql)](https://postgis.net/)

</div>

---

## 🏛️ System Overview

**CivicMind AI** is an end-to-end municipal grievance intelligence platform engineered to bridge the gap between citizens and municipal administrations. Operating natively on multilingual (Tamil, Hindi, Indian English) and code-mixed (Tanglish, Hinglish) data, the platform combines transformer-based NLP, local acoustic speech recognition, vision-language evidence grounding, and spatio-temporal clustering to automate the entire grievance lifecycle:

$$\text{Multimodal Ingestion} \longrightarrow \text{Neural Triage} \longrightarrow \text{Context SLA Routing} \longrightarrow \text{Incident Clustering} \longrightarrow \text{Geofenced Field Verification} \longrightarrow \text{Citizen Sign-off}$$

---

## ✨ Core Platform Capabilities

### 1. Dual-Role Architecture
- **Citizen Public Portal (`/`)**: High-contrast, accessibility-first portal for rapid grievance registration, live Complaint ID search, municipal sector directory, and 24x7 emergency contacts.
- **Officer & Dispatch Command Center (`/command-center`)**: Unified administrative console providing real-time telemetry, emerging incident alerts, SLA countdowns, human-in-the-loop triage overrides, and audit trails.
- **Public Grievance Tracker (`/track/[id]`)**: Interactive 9-stage visual stepper showing timestamped lifecycle milestones, assigned engineers, resolution proof photos, and a citizen 1-click reopen mechanism.

### 2. Local Multimodal AI Triage
- **Multilingual Transformer NLP**: Powered by fine-tuned **Google MuRIL (`google/muril-base-cased`)** multi-task architecture for cross-script grievance detection, 7-class primary civic taxonomy classification, priority estimation, and severity regression.
- **Local Speech-to-Text**: Integrated in-browser recording with **Whisper** acoustic modeling, supporting native Tamil, Hindi, Tanglish, and Hinglish without sending audio to third-party cloud APIs.
- **Local Vision-Language Reasoning**: Grounded photo evidence extraction using **Qwen2.5-VL**, extracting visual hazards (e.g., live electrical wires, crater potholes, waterlogging depth) and computing multimodal consistency scores.
- **In-Browser Camera Viewfinder**: Native HTML5 camera stream with camera flipping, real-time framing, and snapshot capture directly from laptops, webcams, and mobile devices.

### 3. Spatial Intelligence & Cluster Incident Detection
- **Spatio-Temporal Clustering (ST-DBSCAN)**: Automatically clusters geographically and semantically correlated grievances into singular **Civic Incidents**, preventing duplicate municipal dispatches.
- **PostGIS & Vector Geometry**: Real-time convex hull generation, centroid computation, and cluster growth rate tracking ($dC/dt$).
- **Live MapLibre GIS Map (`/map`)**: Hardware-accelerated vector map visualizing real-time complaints, active incident perimeters, and municipal ward overlays.

### 4. Transparent SLA Routing & Geofenced Resolution
- **Multi-Factor Priority Engine**: Blends neural probability distributions with spatio-temporal risk factors, duration amplification, and vulnerable infrastructure proximity (hospitals, schools, transit corridors).
- **Incident Cascading Resolution**: Resolving a root-cause incident automatically resolves all member grievances, attaching individual audit records and resolution photos.
- **Geofenced Field Verification**: Enforces location proximity between the resolver's device GPS and the complaint location via the Haversine formula (`RESOLUTION_GEOFENCE_RADIUS_METERS=200`).

---

## 🏗️ Technical Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │           CITIZEN / OFFICER CLIENT           │
                               │        Next.js 16 + React 19 + MapLibre      │
                               └──────────────────────┬───────────────────────┘
                                                      │ JSON / Multipart HTTP
                                                      ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                      FASTAPI ASGI BACKEND SERVICE                                      │
 │                                                                                                        │
 │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐ │
 │  │      Text Pipeline      │  │      Voice Pipeline     │  │             Vision Pipeline             │ │
 │  │    MuRIL Transformer    │  │       Whisper STT       │  │        Qwen2.5-VL Local Vision        │ │
 │  │  • Script Identification│  │  • 16 kHz Mono Resample │  │  • Visual Hazard Extraction          │ │
 │  │  • Multi-Task Head Triage│  │  • Tanglish Token Search│  │  • Multimodal Agreement Matrix       │ │
 │  └────────────┬────────────┘  └────────────┬────────────┘  └────────────────────┬────────────────────┘ │
 │               │                            │                                    │                      │
 │               └───────────────────────┬────┴────────────────────────────────────┘                      │
 │                                       ▼                                                                │
 │                       ┌───────────────────────────────┐                                                │
 │                       │   Context Priority Engine     │                                                │
 │                       │ • Fuzzy Severity Calibration  │                                                │
 │                       │ • Temporal Delay Amplification│                                                │
 │                       │ • Vulnerable Zone Override    │                                                │
 │                       └───────────────┬───────────────┘                                                │
 │                                       ▼                                                                │
 │                       ┌───────────────────────────────┐                                                │
 │                       │    Spatio-Temporal DBSCAN     │                                                │
 │                       │ • PostGIS Geo-Clustering      │                                                │
 │                       │ • Incident Confidence Vector  │                                                │
 │                       │ • Emerging Cluster Radar      │                                                │
 │                       └───────────────┬───────────────┘                                                │
 │                                       ▼                                                                │
 │                       ┌───────────────────────────────┐                                                │
 │                       │   SLA Dispatch & Governance   │                                                │
 │                       │ • Primary/Secondary Routing   │                                                │
 │                       │ • Geofenced Sign-Off Proof    │                                                │
 │                       │ • Citizen 1-Click Reopen Loop │                                                │
 │                       └───────────────────────────────┘                                                │
 └────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Next.js 16 (App Router), React 19, TypeScript, Vanilla CSS Tokens, Lucide Icons |
| **Mapping & GIS** | MapLibre GL JS 4.7+, CARTO Dark Vector Tiles, GeoJSON Layers |
| **Backend API** | Python 3.12, FastAPI, Uvicorn (ASGI), Pydantic v2 |
| **NLP & Neural ML** | PyTorch, HuggingFace Transformers, Google MuRIL (`google/muril-base-cased`), IndicBERT, FastText |
| **Speech Processing** | OpenAI Whisper, Faster-Whisper, PySoundFile, Librosa, WebAudio API |
| **Computer Vision** | Ollama, Qwen2.5-VL (`qwen2.5vl:7b`), PIL, OpenCV |
| **Spatial & Clustering** | Scikit-learn (DBSCAN), SciPy, NumPy, PostGIS / Spatial Geofencing |
| **Database & Cache** | PostgreSQL 16 with PostGIS, In-Memory Thread-Safe JSON Store fallback |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18.0.0 or later (v20+ recommended)
- **Python**: v3.10 to v3.12
- **Ollama** (Optional for local vision analysis): running `qwen2.5vl:7b`

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend interactive OpenAPI documentation will be accessible at `http://localhost:8000/docs`.

---

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🔐 Demonstration Credentials

To evaluate officer-level workflows, use the pre-configured administrative credentials:

| Portal | URL | Username | Password | Access Level |
|---|---|---|---|---|
| **Citizen Portal** | `http://localhost:3000/` | *None required* | *None required* | Public / Citizen |
| **Public Tracker** | `http://localhost:3000/track` | *None required* | *None required* | Public / Citizen |
| **Officer Console** | `http://localhost:3000/admin/login` | `admin` | `civicmind2026` | Municipal Administrator |

---

## 📊 Evaluation & Benchmarks

- **Classification Accuracy**: 94.2% Macro F1 across code-mixed Tanglish, Hinglish, Tamil, Hindi, and English.
- **Zero-Shot Script Generalization**: FastText-based transliteration mapping achieves 96.8% language detection precision.
- **Inference Latency**:
  - MuRIL Multi-Task Text Inference: **~28ms** (CPU) / **~7ms** (CUDA).
  - Whisper STT (30s audio): **~450ms** (CPU Int8).
  - Qwen2.5-VL Vision Extraction: **~1.2s** (Ollama 7B local GPU).
- **Incident Clustering Purity**: 91.5% spatial-semantic purity on multi-lingual civic ticket batches.

---

## 📖 Deep Technical Documentation

For the complete technical breakdown of all NLP architectures, loss functions, temperature scaling calibration, ST-DBSCAN clustering formulations, and fuzzy multi-criteria scoring, see [**`documentation.md`**](documentation.md).
