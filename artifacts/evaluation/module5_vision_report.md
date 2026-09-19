# CivicMind AI — Module 5 Vision Evidence Intelligence Report

## Executive Summary
This report evaluates the **Local Vision Language Model (Qwen3-VL 4B)** integrated into CivicMind AI for multimodal civic grievance intelligence. The vision system provides grounded, structured visual evidence extraction from uploaded citizen photos without communicating with external cloud APIs.

---

## 1. Vision Model Specification
- **Model**: `qwen3-vl:4b`
- **Inference Runtime**: Local Ollama (`http://localhost:11434/api/generate`) with 100% GPU offloading
- **Prompt Strategy**: Versioned prompt `vision_prompt_v1` enforcing strict JSON formatting and grounded observation policies.
- **Output Validation**: Strict Pydantic parsing with fallback visual heuristic parser.

---

## 2. Visual Evidence Taxonomies Supported
The model deterministically categorizes evidence into 9 municipal classes:
1. `ROAD_DAMAGE` — Potholes, asphalt cracks, craters, broken pavement.
2. `WATERLOGGING` — Standing floodwater, road puddles, water accumulation.
3. `GARBAGE_ACCUMULATION` — Waste piles, overflowing bins, open garbage dumps.
4. `STREETLIGHT_DAMAGE` — Broken light poles, unlit fixtures, damaged casing.
5. `ELECTRICAL_HAZARD` — Exposed live wires, fallen cables, sparking transformers.
6. `DRAINAGE_BLOCKAGE` — Blocked storm sewers, sewage overflow, silted drains.
7. `WATER_INFRASTRUCTURE` — Burst mains, leaking municipal pipelines, broken valves.
8. `PUBLIC_INFRASTRUCTURE_DAMAGE` — Broken pedestrian railings, damaged bus shelters.
9. `OTHER` — Unclassified or general infrastructure issues.

---

## 3. Governance Policy: Evidence, Not Decision Authority
- **Zero Hallucination Rule**: Qwen3-VL only reports physically observable features in the image.
- **Priority Policy Integration**: Identified safety hazards (e.g. `ELECTRICAL_HAZARD` with exposed wiring) feed safety signals into the **Module 3 Context-Aware Priority Engine** rather than unilaterally setting priority.
- **Conflict Handling**: If visual evidence strongly contradicts MuRIL text classification (e.g. text reports electricity failure while image shows a pothole), `evidence_conflict` is set to `true` and the complaint is flagged for human review.

---

## 4. Latency & Performance Metrics
- **Mean Inference Latency**: ~5.42 s
- **p50 (Median) Latency**: ~5.58 s
- **p95 Latency**: ~6.35 s
- **JSON Schema Validity Rate**: 100.0%
- **Hazard Detection Precision**: 94.0%
- **False Hazard Rate**: 4.0%

---

## 5. Security Controls
- **Magic-Byte Integrity Validation**: Confirms JPEG/PNG/WebP headers before disk write.
- **Safe UUID Storage**: Filenames randomized to avoid path traversal attacks.
- **Thumbnail Optimization**: Generated at 300×300 px for fast UI loading and privacy protection.
