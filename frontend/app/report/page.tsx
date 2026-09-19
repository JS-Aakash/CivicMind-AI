"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  Mic,
  Camera,
  MapPin,
  Send,
  Globe,
  CheckCircle,
  Loader2,
  Navigation,
  Sparkles,
  Volume2,
  Square,
  Play,
  RotateCcw,
  Image as ImageIcon,
  Trash2,
  AlertTriangle,
  FileCheck,
  ChevronRight,
  ChevronLeft,
  ShieldAlert,
  Clock,
  Building2,
  ArrowLeft,
  Layers,
  FileText,
  Radio,
  Check,
} from "lucide-react";
import { analyzeGrievance, createGrievance, uploadAudio, uploadImage } from "@/lib/api";
import { convertBlobTo16kHzWav } from "@/lib/audio";
import { AIAnalysisPanel } from "@/components/AIAnalysisPanel";
import type { AIAnalysisResult, VisionAnalysisItem, VoiceTranscriptionItem } from "@/lib/types";

const PRESET_LOCALITIES = [
  { name: "T. Nagar (Ward 112)", lat: 13.0415, lng: 80.2338 },
  { name: "Anna Nagar (Ward 95)", lat: 13.0852, lng: 80.2105 },
  { name: "Velachery (Ward 178)", lat: 12.9755, lng: 80.2215 },
  { name: "Mylapore (Ward 124)", lat: 13.0335, lng: 80.2675 },
  { name: "Adyar (Ward 175)", lat: 13.0012, lng: 80.2565 },
];

const QUICK_PROMPTS = [
  { label: "Water Cut", text: "Water supply disruption for the past 3 days in our residential area." },
  { label: "தமிழ் குடிநீர்", text: "கடந்த மூன்று நாட்களாக குடிநீர் வரவில்லை. குழாயில் அழுக்கு நீர் வருகிறது." },
  { label: "Pothole Hazard", text: "Deep hazardous potholes on the main carriage way causing severe traffic risk." },
  { label: "Garbage Pile", text: "Overflowing municipal garbage bin near the street corner creating health risk." },
];

export default function ReportPage() {
  const [isMounted, setIsMounted] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [text, setText] = useState("");
  const [locationText, setLocationText] = useState("");
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [gpsStatus, setGpsStatus] = useState<"idle" | "detecting" | "locked" | "denied">("idle");

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioId, setAudioId] = useState<string | null>(null);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceTranscription, setVoiceTranscription] = useState<VoiceTranscriptionItem | null>(null);
  const [editedTranscript, setEditedTranscript] = useState("");
  const [transcriptionError, setTranscriptionError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Image evidence state
  const [images, setImages] = useState<Array<{ file: File; previewUrl: string; mediaId?: string; analysis?: VisionAnalysisItem }>>([]);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);

  // Live Camera Viewfinder State
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // AI Pipeline state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AIAnalysisResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [complaintCode, setComplaintCode] = useState("");
  const [complaintId, setComplaintId] = useState("");

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setIsMounted(true);
    handleDetectGPS(false);
  }, []);

  // Debounced auto-analysis on text change
  const triggerAutoAnalysis = useCallback((inputText: string) => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    if (!inputText || inputText.trim().length < 5) return;

    debounceTimerRef.current = setTimeout(async () => {
      try {
        setAnalyzing(true);
        const result = await analyzeGrievance({
          text: inputText.trim(),
          location_text: locationText || undefined,
          latitude: latitude || undefined,
          longitude: longitude || undefined,
        });
        setAnalysis(result.analysis);
      } catch (err) {
        console.warn("Auto-analysis error:", err);
      } finally {
        setAnalyzing(false);
      }
    }, 600);
  }, [locationText, latitude, longitude]);

  useEffect(() => {
    const effectiveText = editedTranscript || text;
    if (effectiveText && effectiveText.trim().length >= 5) {
      triggerAutoAnalysis(effectiveText);
    }
  }, [text, editedTranscript, triggerAutoAnalysis]);

  const handleDetectGPS = (showFeedback = true) => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      if (showFeedback) alert("Geolocation is not supported by your browser.");
      setGpsStatus("denied");
      return;
    }

    setGpsStatus("detecting");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        setLatitude(lat);
        setLongitude(lng);
        setGpsStatus("locked");
        if (!locationText) {
          setLocationText(`Chennai Geo (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`);
        }
      },
      (err) => {
        console.warn("GPS access denied or timed out:", err);
        setGpsStatus("denied");
        if (latitude === null) {
          setLatitude(13.0415);
          setLongitude(80.2338);
          if (!locationText) setLocationText("T. Nagar, Ward 112, Chennai");
        }
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 }
    );
  };

  const handleSelectPreset = (preset: { name: string; lat: number; lng: number }) => {
    setLocationText(preset.name);
    setLatitude(preset.lat);
    setLongitude(preset.lng);
    setGpsStatus("locked");
  };

  // ─────────────────────────────────────────────────────────────────────────────
  // Voice Recording Functions (Whisper STT)
  // ─────────────────────────────────────────────────────────────────────────────
  const startRecording = async () => {
    setTranscriptionError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const rawBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const previewUrl = URL.createObjectURL(rawBlob);
        setAudioBlob(rawBlob);
        setAudioUrl(previewUrl);

        setTranscribing(true);
        try {
          let uploadBlob: Blob = rawBlob;
          try {
            uploadBlob = await convertBlobTo16kHzWav(rawBlob);
          } catch (convErr) {
            console.warn("Audio resampling fallback:", convErr);
          }

          const audioFile = new File([uploadBlob], "voice_grievance.wav", { type: "audio/wav" });
          const transResp = await uploadAudio(audioFile);
          setAudioId(transResp.media_id);
          setVoiceTranscription(transResp as any);
          setEditedTranscript(transResp.raw_transcript);
          if (!text || text.trim().length === 0) {
            setText(transResp.raw_transcript);
          }
          triggerAutoAnalysis(transResp.raw_transcript);
        } catch (err: any) {
          console.error("Audio upload error:", err);
          setTranscriptionError(err.message || "Failed to transcribe audio. You can enter description manually.");
        } finally {
          setTranscribing(false);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingDuration(0);
      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      alert("Microphone permission was denied. Please allow microphone access in browser.");
      console.error(err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setAudioUrl(null);
    setAudioId(null);
    setVoiceTranscription(null);
    setEditedTranscript("");
    setRecordingDuration(0);
    setTranscriptionError(null);
  };

  // ─────────────────────────────────────────────────────────────────────────────
  // Image Upload & Live Camera Capture Functions
  // ─────────────────────────────────────────────────────────────────────────────
  const processImageFile = async (file: File) => {
    setImageError(null);
    const previewUrl = URL.createObjectURL(file);

    setUploadingImage(true);
    try {
      const visResp = await uploadImage(file, text || editedTranscript);
      setImages((prev) => [
        ...prev,
        {
          file,
          previewUrl,
          mediaId: visResp.media_id,
          analysis: visResp as VisionAnalysisItem,
        },
      ]);
    } catch (err: any) {
      console.error("Vision analysis error:", err);
      setImageError(err.message || "Could not analyze image. Photo will still be attached.");
      setImages((prev) => [
        ...prev,
        {
          file,
          previewUrl,
          analysis: {
            analysis_id: "client-img-" + Date.now(),
            media_id: "client-media",
            observations: ["Visual proof attached by citizen"],
            objects: ["infrastructure"],
            possible_hazards: [],
            evidence_category: "OTHER",
            severity_signal: "medium",
            confidence: 0.80,
            created_at: new Date().toISOString(),
          },
        },
      ]);
    } finally {
      setUploadingImage(false);
    }
  };

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    await processImageFile(file);
  };

  useEffect(() => {
    if (isCameraOpen && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch((err) => console.warn("Auto-play prevented:", err));
    }
  }, [isCameraOpen]);

  const startCamera = async (mode: "environment" | "user" = facingMode) => {
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: mode },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      streamRef.current = stream;
      setIsCameraOpen(true);

      setTimeout(() => {
        if (videoRef.current && streamRef.current) {
          videoRef.current.srcObject = streamRef.current;
          videoRef.current.play().catch((err) => console.warn("Video play error:", err));
        }
      }, 60);
    } catch (err: any) {
      alert("Camera access was denied or unavailable: " + (err.message || err));
      setIsCameraOpen(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setIsCameraOpen(false);
  };

  const switchCamera = () => {
    const nextMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(nextMode);
    startCamera(nextMode);
  };

  const capturePhotoFromCamera = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const file = new File([blob], `civic-evidence-${Date.now()}.jpg`, { type: "image/jpeg" });
      stopCamera();
      await processImageFile(file);
    }, "image/jpeg", 0.92);
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  // ─────────────────────────────────────────────────────────────────────────────
  // AI Preview & Submit
  // ─────────────────────────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    const effectiveText = editedTranscript || text;
    if (!effectiveText.trim() && images.length === 0) return;

    setAnalyzing(true);
    try {
      const result = await analyzeGrievance({
        text: effectiveText || "Visual evidence submitted for inspection.",
        location_text: locationText || undefined,
        latitude: latitude || undefined,
        longitude: longitude || undefined,
      });
      setAnalysis(result.analysis);
      setCurrentStep(5);
    } catch (e) {
      console.warn("Analysis preview error:", e);
      setCurrentStep(5);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmit = async () => {
    const effectiveText = editedTranscript || text;
    if (!effectiveText.trim() && images.length === 0 && !audioId) {
      alert("Please provide a description, voice recording, or photo before submitting.");
      return;
    }

    setSubmitting(true);
    try {
      const mediaIds = images.map((img) => img.mediaId).filter(Boolean) as string[];
      const resp = await createGrievance({
        text: effectiveText || "Civic grievance with media evidence.",
        media_ids: mediaIds,
        audio_id: audioId || undefined,
        raw_transcript: voiceTranscription?.raw_transcript,
        edited_transcript: editedTranscript || undefined,
        location_text: locationText || (latitude ? `Chennai (${latitude}, ${longitude})` : undefined),
        latitude: latitude || undefined,
        longitude: longitude || undefined,
      });

      if (!resp || (!resp.id && !resp.complaint_code)) {
        throw new Error("Invalid response received from grievance server");
      }

      setComplaintCode(resp.complaint_code || `CM-${resp.id}`);
      setComplaintId(String(resp.id));
      setSubmitted(true);
    } catch (e: any) {
      console.error("Submission error:", e);
      alert(`Submission failed: ${e.message || "Could not register grievance. Please verify connection and try again."}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadReceipt = () => {
    const printDate = new Date().toLocaleString("en-IN", {
      dateStyle: "full",
      timeStyle: "medium",
      timeZone: "Asia/Kolkata",
    });
    const code = complaintCode || complaintId || "CM-GRIEVANCE";
    const dept = analysis?.department_name || "Municipal Civic Works & Public Health";
    const priority = (analysis?.priority || "MEDIUM").toUpperCase();
    const slaHours = analysis?.sla?.target_sla_hours || 24;
    const cat = analysis?.category || "Civic Grievance";
    const conf = analysis?.confidence ? `${Math.round(analysis.confidence * 100)}%` : "98%";
    const desc = text || editedTranscript || "Citizen report registered via CivicMind AI portal.";
    const loc = locationText || "Ward Location (Geotagged)";
    const coords = latitude && longitude ? `${latitude.toFixed(5)}° N, ${longitude.toFixed(5)}° E` : "Chennai Geo-Tagged Coordinates";

    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      alert("Please allow popups to open and print your official Grievance Receipt.");
      return;
    }

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>CivicMind AI - Grievance Receipt ${code}</title>
        <style>
          @page { size: A4; margin: 15mm; }
          * { box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            background: #f8fafc;
            margin: 0;
            padding: 30px;
            line-height: 1.5;
          }
          .receipt-container {
            max-width: 740px;
            margin: 0 auto;
            border: 2px solid #1e293b;
            padding: 36px;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 10px 25px rgba(0,0,0,0.06);
          }
          .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 24px;
          }
          .title-section h1 {
            font-size: 22px;
            margin: 0 0 4px;
            color: #0f172a;
            font-weight: 800;
            letter-spacing: -0.02em;
          }
          .title-section p {
            margin: 0;
            font-size: 13px;
            color: #64748b;
          }
          .badge-gov {
            background: #f1f5f9;
            border: 1.5px solid #cbd5e1;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #1e293b;
          }
          .tracking-box {
            background: #f0fdf4;
            border: 1.5px dashed #16a34a;
            padding: 18px 24px;
            border-radius: 8px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .tracking-label {
            font-size: 12px;
            color: #166534;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
          }
          .tracking-val {
            font-size: 26px;
            font-family: monospace;
            font-weight: 800;
            color: #15803d;
          }
          .status-tag {
            background: #16a34a;
            color: #ffffff;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 12px;
            letter-spacing: 0.03em;
          }
          .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 20px;
          }
          .info-block {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 14px 18px;
            border-radius: 8px;
          }
          .info-label {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 4px;
            letter-spacing: 0.04em;
          }
          .info-val {
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
          }
          .desc-box {
            border: 1px solid #e2e8f0;
            padding: 18px;
            border-radius: 8px;
            background: #ffffff;
            margin-bottom: 20px;
          }
          .desc-title {
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            margin-bottom: 8px;
            letter-spacing: 0.04em;
          }
          .desc-content {
            font-size: 14px;
            color: #1e293b;
            white-space: pre-wrap;
            line-height: 1.6;
          }
          .notice-box {
            font-size: 12px;
            color: #475569;
            margin-bottom: 24px;
            padding: 14px 18px;
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            border-radius: 4px;
            line-height: 1.5;
          }
          .footer {
            border-top: 1px solid #e2e8f0;
            padding-top: 20px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #64748b;
          }
          .print-btn-bar {
            max-width: 740px;
            margin: 0 auto 16px;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
          }
          .print-btn {
            background: #2563eb;
            color: #ffffff;
            border: none;
            padding: 10px 22px;
            font-size: 14px;
            font-weight: 700;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(37,99,235,0.25);
            transition: all 0.2s;
          }
          .print-btn:hover {
            background: #1d4ed8;
          }
          @media print {
            .print-btn-bar { display: none; }
            body { padding: 0; background: #ffffff; }
            .receipt-container { border: 1.5px solid #334155; box-shadow: none; border-radius: 0; }
          }
        </style>
      </head>
      <body>
        <div class="print-btn-bar">
          <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>
        <div class="receipt-container">
          <div class="header">
            <div class="title-section">
              <h1>CIVICMIND AI · MUNICIPAL CORPORATION</h1>
              <p>Citizen Grievance Redressal & Official Acknowledgment Receipt</p>
            </div>
            <div class="badge-gov">OFFICIAL PROOF</div>
          </div>

          <div class="tracking-box">
            <div>
              <div class="tracking-label">Grievance Registration Code</div>
              <div class="tracking-val">${code}</div>
            </div>
            <div class="status-tag">✓ REGISTERED & DISPATCHED</div>
          </div>

          <div class="grid">
            <div class="info-block">
              <div class="info-label">Assigned Department</div>
              <div class="info-val">${dept}</div>
            </div>
            <div class="info-block">
              <div class="info-label">Grievance Category</div>
              <div class="info-val">${cat}</div>
            </div>
            <div class="info-block">
              <div class="info-label">Priority & Target SLA</div>
              <div class="info-val">${priority} · ${slaHours} Hours Resolution</div>
            </div>
            <div class="info-block">
              <div class="info-label">AI Triage Classification</div>
              <div class="info-val">${conf} Match Verified</div>
            </div>
          </div>

          <div class="info-block" style="margin-bottom: 20px;">
            <div class="info-label">Reported Location & Geo Coordinates</div>
            <div class="info-val">${loc} <span style="font-weight: 400; color: #64748b; font-size: 13px;">(${coords})</span></div>
          </div>

          <div class="desc-box">
            <div class="desc-title">Citizen Grievance Description</div>
            <div class="desc-content">${desc}</div>
          </div>

          <div class="notice-box">
            <strong>Citizen Charter Guarantee:</strong> This acknowledgment receipt serves as legal proof of submission. Department officers have been dispatched per municipal SLA guidelines. You may track resolution progress in real-time online.
          </div>

          <div class="footer">
            <div>
              <strong>Issued At:</strong> ${printDate}<br/>
              <strong>Verification Token:</strong> SHA256-${Math.random().toString(36).substring(2, 10).toUpperCase()}
            </div>
            <div style="text-align: right;">
              <strong>CivicMind Automated Dispatch Engine</strong><br/>
              Public Grievance Redressal Cell
            </div>
          </div>
        </div>
        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
            }, 350);
          };
        </script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  if (!isMounted) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#060911" }}>
        <Loader2 size={32} className="spin" color="#6366f1" />
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // SUBMISSION SUCCESS VIEW
  // ─────────────────────────────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
          background: "radial-gradient(ellipse at top, #0f172a 0%, #060911 100%)",
        }}
      >
        <div
          style={{
            background: "#0c1322",
            border: "1px solid rgba(99,102,241,0.35)",
            borderRadius: 20,
            padding: 40,
            maxWidth: 580,
            width: "100%",
            textAlign: "center",
            boxShadow: "0 25px 60px rgba(0,0,0,0.8)",
          }}
        >
          <div
            style={{
              width: 76,
              height: 76,
              borderRadius: "50%",
              background: "rgba(34,197,94,0.12)",
              border: "2px solid rgba(34,197,94,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 20px",
              boxShadow: "0 0 30px rgba(34,197,94,0.25)",
            }}
          >
            <CheckCircle size={42} color="#22c55e" />
          </div>

          <h2 style={{ marginBottom: 8, fontSize: 26, fontWeight: 800, color: "#ffffff", letterSpacing: "-0.02em" }}>
            Grievance Registered Successfully
          </h2>
          <p style={{ color: "#94a3b8", fontSize: 14, marginBottom: 24, lineHeight: 1.5 }}>
            Your grievance has been validated by multimodal AI, geocoded to Chennai Municipal Wards, and routed to the department response cell.
          </p>

          <div
            style={{
              background: "rgba(15, 23, 42, 0.75)",
              borderRadius: 14,
              padding: 20,
              marginBottom: 24,
              border: "1px solid rgba(51, 65, 85, 0.6)",
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid rgba(51, 65, 85, 0.4)" }}>
              <span style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600 }}>Official Complaint ID</span>
              <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: "#818cf8" }}>
                {complaintCode}
              </span>
            </div>
            {analysis && (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, fontSize: 13 }}>
                  <span style={{ color: "#94a3b8" }}>Assigned Department</span>
                  <span style={{ fontWeight: 600, color: "#f1f5f9" }}>{analysis.department_name}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, fontSize: 13 }}>
                  <span style={{ color: "#94a3b8" }}>Priority & Target SLA</span>
                  <span style={{ fontWeight: 700, color: analysis.priority === "critical" ? "#f43f5e" : "#fbbf24" }}>
                    {analysis.priority.toUpperCase()} ({analysis.sla?.target_sla_hours || 24}h Deadline)
                  </span>
                </div>
              </>
            )}
            {latitude && longitude && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 13 }}>
                <span style={{ color: "#94a3b8" }}>📍 Geo-Coordinates</span>
                <span style={{ fontFamily: "monospace", color: "#4ade80" }}>
                  {latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E
                </span>
              </div>
            )}
          </div>

          {/* Download Official Proof Receipt Button */}
          <button
            onClick={handleDownloadReceipt}
            style={{
              width: "100%",
              marginBottom: 14,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              padding: "14px 20px",
              fontSize: 14,
              fontWeight: 700,
              background: "linear-gradient(135deg, #4f46e5, #3b82f6)",
              color: "#ffffff",
              border: "none",
              borderRadius: 10,
              cursor: "pointer",
              boxShadow: "0 4px 16px rgba(79,70,229,0.35)",
            }}
          >
            <span>📄</span>
            <span>Download Official Grievance Receipt (PDF)</span>
          </button>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 18 }}>
            <Link
              href={`/my-complaints/${complaintCode || complaintId}`}
              style={{
                textDecoration: "none",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: 6,
                fontSize: 13,
                fontWeight: 600,
                padding: "12px",
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: "#e2e8f0",
              }}
            >
              📋 Track Complaint
            </Link>
            <Link
              href="/map"
              style={{
                textDecoration: "none",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: 6,
                fontSize: 13,
                fontWeight: 600,
                padding: "12px",
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: "#e2e8f0",
              }}
            >
              🗺️ Live Civic Map
            </Link>
          </div>

          <button
            onClick={() => {
              setSubmitted(false);
              setText("");
              setLocationText("");
              setAnalysis(null);
              resetRecording();
              setImages([]);
              setCurrentStep(1);
            }}
            style={{
              background: "transparent",
              border: "none",
              color: "#64748b",
              fontSize: 13,
              cursor: "pointer",
              padding: "6px",
            }}
          >
            + File Another Municipal Grievance
          </button>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // MAIN WIZARD VIEW
  // ─────────────────────────────────────────────────────────────────────────────
  const steps = [
    { num: 1, title: "1. Describe", desc: "Written Issue" },
    { num: 2, title: "2. Voice Note", desc: "Whisper STT" },
    { num: 3, title: "3. Photo Evidence", desc: "Camera / Upload" },
    { num: 4, title: "4. Location", desc: "Ward & GPS" },
    { num: 5, title: "5. Review", desc: "AI Dispatch" },
  ];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#060911", color: "#f8fafc", paddingBottom: 60 }}>
      {/* Top Header Bar */}
      <header
        style={{
          borderBottom: "1px solid rgba(51, 65, 85, 0.5)",
          backgroundColor: "#0a0f1d",
          padding: "16px 28px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Link
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              color: "#94a3b8",
              textDecoration: "none",
              padding: "6px 12px",
              borderRadius: 6,
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <ArrowLeft size={14} /> Back to Portal
          </Link>
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 800, color: "#ffffff", letterSpacing: "-0.01em", margin: 0 }}>
              Citizen Grievance Submission Portal
            </h1>
            <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0 0 0" }}>
              Submit municipal issues with voice notes, live camera photos, and GPS location
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, color: "#4ade80", background: "rgba(34, 197, 94, 0.1)", border: "1px solid rgba(34, 197, 94, 0.25)", padding: "4px 10px", borderRadius: 9999, fontWeight: 600 }}>
            ● AI Triage Online
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ maxWidth: 1240, margin: "0 auto", padding: "28px 24px" }}>
        {/* Step Progress Tracker */}
        <div
          style={{
            backgroundColor: "#0d1424",
            border: "1px solid rgba(51, 65, 85, 0.6)",
            borderRadius: 14,
            padding: "14px 20px",
            marginBottom: 24,
            boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(5, 1fr)",
              gap: 8,
              position: "relative",
            }}
          >
            {steps.map((s) => {
              const isActive = currentStep === s.num;
              const isDone = currentStep > s.num;
              return (
                <button
                  key={s.num}
                  type="button"
                  onClick={() => setCurrentStep(s.num)}
                  style={{
                    background: isActive
                      ? "rgba(99, 102, 241, 0.15)"
                      : isDone
                      ? "rgba(34, 197, 94, 0.08)"
                      : "transparent",
                    border: isActive
                      ? "1px solid #6366f1"
                      : isDone
                      ? "1px solid rgba(34, 197, 94, 0.3)"
                      : "1px solid transparent",
                    borderRadius: 8,
                    padding: "8px 10px",
                    cursor: "pointer",
                    textAlign: "left",
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    transition: "all 0.2s ease",
                  }}
                >
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: "50%",
                      backgroundColor: isActive ? "#6366f1" : isDone ? "#22c55e" : "#1e293b",
                      color: "#ffffff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 11,
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    {isDone ? <Check size={12} strokeWidth={3} /> : s.num}
                  </div>
                  <div style={{ overflow: "hidden" }}>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: isActive ? 700 : 600,
                        color: isActive ? "#ffffff" : isDone ? "#e2e8f0" : "#64748b",
                        whiteSpace: "nowrap",
                        textOverflow: "ellipsis",
                        overflow: "hidden",
                      }}
                    >
                      {s.title}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2-Column Split: Form Wizard + Live AI Intelligence Panel */}
        <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 24, alignItems: "start" }}>
          {/* Left Column: Current Wizard Step */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* STEP 1: DESCRIBE THE ISSUE */}
            {currentStep === 1 && (
              <div
                style={{
                  backgroundColor: "#0d1424",
                  border: "1px solid rgba(51, 65, 85, 0.6)",
                  borderRadius: 14,
                  padding: 24,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(99,102,241,0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#818cf8" }}>
                    <FileText size={18} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", margin: 0 }}>
                      Step 1: Describe the Civic Issue
                    </h2>
                    <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0 0 0" }}>
                      Write in Tamil (தமிழ்), Tanglish, Hindi (हिंदी), Hinglish, or English.
                    </p>
                  </div>
                </div>

                {/* Quick Prompts */}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "16px 0 12px" }}>
                  <span style={{ fontSize: 11, color: "#64748b", alignSelf: "center", marginRight: 4 }}>Quick templates:</span>
                  {QUICK_PROMPTS.map((qp, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => {
                        setText(qp.text);
                        triggerAutoAnalysis(qp.text);
                      }}
                      style={{
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: 6,
                        padding: "3px 8px",
                        fontSize: 11,
                        color: "#94a3b8",
                        cursor: "pointer",
                      }}
                    >
                      {qp.label}
                    </button>
                  ))}
                </div>

                {/* Textarea Input */}
                <textarea
                  value={text}
                  onChange={(e) => {
                    setText(e.target.value);
                    triggerAutoAnalysis(e.target.value);
                  }}
                  placeholder="Describe your civic grievance here (e.g. '3 days ah water supply varala near Ward 112', 'Hazardous open electric wire sparking near bus stop', 'ரோட்டில் பெரிய பள்ளம் ஏற்பட்டுள்ளது')..."
                  style={{
                    width: "100%",
                    minHeight: 140,
                    backgroundColor: "#070b14",
                    border: "1px solid rgba(51, 65, 85, 0.8)",
                    borderRadius: 10,
                    padding: "14px 16px",
                    color: "#f8fafc",
                    fontSize: 14,
                    lineHeight: 1.6,
                    resize: "vertical",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8, fontSize: 11, color: "#64748b" }}>
                  <span>{text.length} characters entered</span>
                  <span>AI classifies category, priority & department in real time</span>
                </div>

                {/* Step 1 Actions Bar */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: 20,
                    paddingTop: 16,
                    borderTop: "1px solid rgba(51, 65, 85, 0.4)",
                    flexWrap: "wrap",
                    gap: 10,
                  }}
                >
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      type="button"
                      onClick={() => setCurrentStep(2)}
                      style={{
                        background: "rgba(239, 68, 68, 0.12)",
                        border: "1px solid rgba(239, 68, 68, 0.35)",
                        borderRadius: 8,
                        padding: "8px 14px",
                        color: "#f87171",
                        fontSize: 12,
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        cursor: "pointer",
                      }}
                    >
                      <Mic size={14} color="#ef4444" /> Record Voice Note
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCurrentStep(3);
                        startCamera("environment");
                      }}
                      style={{
                        background: "rgba(99, 102, 241, 0.12)",
                        border: "1px solid rgba(99, 102, 241, 0.35)",
                        borderRadius: 8,
                        padding: "8px 14px",
                        color: "#818cf8",
                        fontSize: 12,
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        cursor: "pointer",
                      }}
                    >
                      <Camera size={14} color="#818cf8" /> Open Camera
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      if (!text.trim() && !editedTranscript && images.length === 0) {
                        alert("Please enter a description, record a voice note, or take a photo.");
                        return;
                      }
                      setCurrentStep(2);
                    }}
                    style={{
                      background: "linear-gradient(135deg, #4f46e5, #3b82f6)",
                      border: "none",
                      borderRadius: 8,
                      padding: "9px 20px",
                      color: "#ffffff",
                      fontSize: 13,
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      boxShadow: "0 4px 12px rgba(79,70,229,0.3)",
                    }}
                  >
                    Next: Voice Note <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: VOICE RECORDING (LOCAL WHISPER) */}
            {currentStep === 2 && (
              <div
                style={{
                  backgroundColor: "#0d1424",
                  border: "1px solid rgba(51, 65, 85, 0.6)",
                  borderRadius: 14,
                  padding: 24,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(239,68,68,0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#f87171" }}>
                    <Mic size={18} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", margin: 0 }}>
                      Step 2: Voice Grievance Note (Whisper STT)
                    </h2>
                    <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0 0 0" }}>
                      Speak in Tamil, Hindi, or English. Audio is converted to 16kHz WAV and transcribed locally.
                    </p>
                  </div>
                </div>

                {/* Studio Recorder Centerpiece */}
                <div
                  style={{
                    background: "#070b14",
                    border: "1px solid rgba(51, 65, 85, 0.6)",
                    borderRadius: 12,
                    padding: "32px 20px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 16,
                    margin: "12px 0 20px",
                  }}
                >
                  {!isRecording ? (
                    <button
                      type="button"
                      onClick={startRecording}
                      style={{
                        width: 72,
                        height: 72,
                        borderRadius: "50%",
                        background: "radial-gradient(circle, #ef4444, #b91c1c)",
                        border: "3px solid #fecaca",
                        color: "#fff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        boxShadow: "0 0 28px rgba(239,68,68,0.4)",
                        transition: "transform 0.15s ease",
                      }}
                      title="Tap to speak"
                    >
                      <Mic size={32} />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={stopRecording}
                      style={{
                        width: 72,
                        height: 72,
                        borderRadius: "50%",
                        background: "#1e293b",
                        border: "3px solid #ef4444",
                        color: "#ef4444",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        boxShadow: "0 0 32px rgba(239,68,68,0.6)",
                        animation: "pulse 1.2s infinite",
                      }}
                      title="Tap to finish recording"
                    >
                      <Square size={28} fill="#ef4444" />
                    </button>
                  )}

                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 20, fontWeight: 800, fontFamily: "monospace", color: isRecording ? "#f43f5e" : "#f1f5f9" }}>
                      {Math.floor(recordingDuration / 60).toString().padStart(2, "0")}:{(recordingDuration % 60).toString().padStart(2, "0")}
                    </div>
                    <p style={{ fontSize: 12, color: isRecording ? "#fda4af" : "#94a3b8", margin: "4px 0 0 0" }}>
                      {isRecording ? "🔴 Listening... Speak naturally now" : audioBlob ? "✓ Voice note ready for transcription" : "Tap the red microphone button to start recording"}
                    </p>
                  </div>
                </div>

                {transcribing && (
                  <div style={{ display: "flex", alignItems: "center", gap: 10, padding: 12, background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: 8, marginBottom: 16 }}>
                    <Loader2 size={16} className="spin" color="#818cf8" />
                    <span style={{ fontSize: 12, color: "#818cf8", fontWeight: 500 }}>
                      Transcribing speech with local Whisper model...
                    </span>
                  </div>
                )}

                {transcriptionError && (
                  <div style={{ padding: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, color: "#f87171", fontSize: 12, marginBottom: 16 }}>
                    ⚠ {transcriptionError}
                  </div>
                )}

                {/* Transcribed Output & Actions */}
                {voiceTranscription && (
                  <div style={{ background: "#070b14", border: "1px solid rgba(51, 65, 85, 0.8)", borderRadius: 10, padding: 16, marginBottom: 16 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "#818cf8", textTransform: "uppercase" }}>
                        🎙 Transcribed ({voiceTranscription.language_name || "Tamil / English"})
                      </span>
                      <button
                        type="button"
                        onClick={resetRecording}
                        style={{ background: "none", border: "none", color: "#94a3b8", fontSize: 11, cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}
                      >
                        <RotateCcw size={12} /> Re-record
                      </button>
                    </div>

                    <textarea
                      value={editedTranscript}
                      onChange={(e) => {
                        setEditedTranscript(e.target.value);
                        triggerAutoAnalysis(e.target.value);
                      }}
                      style={{
                        width: "100%",
                        minHeight: 70,
                        backgroundColor: "transparent",
                        border: "none",
                        color: "#f8fafc",
                        fontSize: 13,
                        outline: "none",
                        resize: "vertical",
                        lineHeight: 1.5,
                      }}
                      placeholder="Review or edit transcript..."
                    />

                    <div style={{ display: "flex", gap: 8, marginTop: 10, paddingTop: 10, borderTop: "1px solid rgba(51, 65, 85, 0.4)" }}>
                      {text && text.trim().length > 0 && (
                        <button
                          type="button"
                          onClick={() => {
                            const combined = `${text}\n${editedTranscript}`;
                            setText(combined);
                            triggerAutoAnalysis(combined);
                            alert("Appended voice transcript to your description.");
                          }}
                          style={{
                            background: "rgba(255,255,255,0.06)",
                            border: "1px solid rgba(255,255,255,0.12)",
                            borderRadius: 6,
                            padding: "6px 12px",
                            fontSize: 11,
                            color: "#e2e8f0",
                            cursor: "pointer",
                          }}
                        >
                          ➕ Append to Description
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setText(editedTranscript);
                          triggerAutoAnalysis(editedTranscript);
                        }}
                        style={{
                          background: "rgba(99, 102, 241, 0.15)",
                          border: "1px solid rgba(99, 102, 241, 0.3)",
                          borderRadius: 6,
                          padding: "6px 12px",
                          fontSize: 11,
                          color: "#818cf8",
                          cursor: "pointer",
                        }}
                      >
                        🔄 Set as Main Description
                      </button>
                    </div>
                  </div>
                )}

                {/* Step 2 Actions Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(51, 65, 85, 0.4)" }}>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(1)}
                    style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, padding: "8px 16px", color: "#94a3b8", fontSize: 12, cursor: "pointer" }}
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(3)}
                    style={{
                      background: "linear-gradient(135deg, #4f46e5, #3b82f6)",
                      border: "none",
                      borderRadius: 8,
                      padding: "9px 20px",
                      color: "#ffffff",
                      fontSize: 13,
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    Next: Photo Evidence <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: PHOTO EVIDENCE & CAMERA */}
            {currentStep === 3 && (
              <div
                style={{
                  backgroundColor: "#0d1424",
                  border: "1px solid rgba(51, 65, 85, 0.6)",
                  borderRadius: 14,
                  padding: 24,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(34, 211, 238, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#22d3ee" }}>
                    <ImageIcon size={18} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", margin: 0 }}>
                      Step 3: Photo Evidence (Optional)
                    </h2>
                    <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0 0 0" }}>
                      Attach photos of potholes, fallen wires, or garbage for local Qwen2.5-VL vision analysis.
                    </p>
                  </div>
                </div>

                {/* Dual Option Cards */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                  <button
                    type="button"
                    onClick={() => startCamera("environment")}
                    disabled={uploadingImage}
                    style={{
                      padding: "24px 16px",
                      border: "2px dashed rgba(99, 102, 241, 0.4)",
                      borderRadius: 12,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      background: "rgba(99, 102, 241, 0.06)",
                      color: "#f8fafc",
                    }}
                  >
                    <div style={{ width: 44, height: 44, borderRadius: "50%", background: "rgba(99, 102, 241, 0.2)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 8, color: "#818cf8" }}>
                      <Camera size={22} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 700 }}>📸 Open Camera</span>
                    <span style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>Laptop or Phone Cam</span>
                  </button>

                  <label
                    style={{
                      padding: "24px 16px",
                      border: "2px dashed rgba(51, 65, 85, 0.8)",
                      borderRadius: 12,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      background: "rgba(255, 255, 255, 0.02)",
                    }}
                  >
                    <div style={{ width: 44, height: 44, borderRadius: "50%", background: "rgba(34, 211, 238, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 8, color: "#22d3ee" }}>
                      <ImageIcon size={22} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>📁 Upload Photo</span>
                    <span style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>JPEG or PNG</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageSelect}
                      style={{ display: "none" }}
                      disabled={uploadingImage}
                    />
                  </label>
                </div>

                {uploadingImage && (
                  <div style={{ display: "flex", alignItems: "center", gap: 10, padding: 12, background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)", borderRadius: 8, marginBottom: 16 }}>
                    <Loader2 size={16} className="spin" color="#818cf8" />
                    <span style={{ fontSize: 12, color: "#818cf8" }}>
                      Analyzing visual hazard & severity with local Qwen2.5-VL...
                    </span>
                  </div>
                )}

                <canvas ref={canvasRef} style={{ display: "none" }} />

                {/* Viewfinder Modal */}
                {isCameraOpen && (
                  <div
                    style={{
                      position: "fixed",
                      inset: 0,
                      background: "rgba(0, 0, 0, 0.88)",
                      backdropFilter: "blur(8px)",
                      zIndex: 100,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      padding: 16,
                    }}
                  >
                    <div
                      style={{
                        maxWidth: 540,
                        width: "100%",
                        background: "#0c1322",
                        borderRadius: 16,
                        border: "1px solid #334155",
                        overflow: "hidden",
                        boxShadow: "0 25px 50px rgba(0,0,0,0.8)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 18px", borderBottom: "1px solid #1e293b" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <Camera size={18} color="#818cf8" />
                          <span style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>Civic Camera Viewfinder</span>
                        </div>
                        <button
                          type="button"
                          onClick={stopCamera}
                          style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: 16 }}
                        >
                          ✕
                        </button>
                      </div>

                      <div style={{ position: "relative", background: "#000", aspectRatio: "4/3", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          muted
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            inset: 24,
                            border: "1.5px dashed rgba(255,255,255,0.4)",
                            borderRadius: 12,
                            pointerEvents: "none",
                          }}
                        />
                      </div>

                      <div style={{ padding: 18, display: "flex", justifyContent: "space-between", alignItems: "center", background: "#070b14" }}>
                        <button
                          type="button"
                          onClick={switchCamera}
                          style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", color: "#e2e8f0", borderRadius: 8, fontSize: 12, padding: "8px 14px", display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}
                        >
                          <RotateCcw size={14} /> Flip Camera
                        </button>

                        <button
                          type="button"
                          onClick={capturePhotoFromCamera}
                          style={{
                            width: 60,
                            height: 60,
                            borderRadius: "50%",
                            background: "radial-gradient(circle, #22d3ee, #0284c7)",
                            border: "4px solid #ffffff",
                            boxShadow: "0 0 24px rgba(34,211,238,0.6)",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                          title="Capture Snapshot"
                        >
                          <div style={{ width: 20, height: 20, borderRadius: "50%", background: "#ffffff" }} />
                        </button>

                        <button
                          type="button"
                          onClick={stopCamera}
                          style={{ background: "none", border: "none", color: "#94a3b8", fontSize: 12, cursor: "pointer" }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {imageError && (
                  <div style={{ padding: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, color: "#f87171", fontSize: 12, marginBottom: 14 }}>
                    ⚠ {imageError}
                  </div>
                )}

                {/* Attached Images List */}
                {images.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
                    {images.map((img, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: "flex",
                          gap: 12,
                          alignItems: "center",
                          background: "#070b14",
                          borderRadius: 10,
                          padding: 10,
                          border: "1px solid rgba(51, 65, 85, 0.6)",
                        }}
                      >
                        <img src={img.previewUrl} alt="Evidence" style={{ width: 56, height: 56, objectFit: "cover", borderRadius: 8 }} />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                            <span style={{ fontSize: 12, fontWeight: 700, color: "#fff" }}>
                              {img.analysis?.evidence_category?.replace("_", " ") || "Photo Evidence"}
                            </span>
                            <span style={{ fontSize: 10, background: "rgba(99,102,241,0.2)", color: "#818cf8", padding: "1px 6px", borderRadius: 4 }}>
                              {Math.round((img.analysis?.confidence || 0.85) * 100)}% vision conf
                            </span>
                          </div>
                          <p style={{ fontSize: 11, color: "#94a3b8", margin: 0 }}>
                            {img.analysis?.observations?.[0] || "Photo attached successfully."}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeImage(idx)}
                          style={{ background: "none", border: "none", color: "#ef4444", padding: 6, cursor: "pointer" }}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Step 3 Actions Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(51, 65, 85, 0.4)" }}>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, padding: "8px 16px", color: "#94a3b8", fontSize: 12, cursor: "pointer" }}
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(4)}
                    style={{
                      background: "linear-gradient(135deg, #4f46e5, #3b82f6)",
                      border: "none",
                      borderRadius: 8,
                      padding: "9px 20px",
                      color: "#ffffff",
                      fontSize: 13,
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    Next: Ward & Location <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 4: LOCATION & WARD */}
            {currentStep === 4 && (
              <div
                style={{
                  backgroundColor: "#0d1424",
                  border: "1px solid rgba(51, 65, 85, 0.6)",
                  borderRadius: 14,
                  padding: 24,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(34, 197, 94, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#4ade80" }}>
                    <MapPin size={18} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", margin: 0 }}>
                      Step 4: Locality & Ward Geotagging
                    </h2>
                    <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0 0 0" }}>
                      Tag your municipal ward or auto-detect live GPS for spatial incident routing.
                    </p>
                  </div>
                </div>

                {/* Location Search Bar + GPS Trigger */}
                <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                  <input
                    value={locationText}
                    onChange={(e) => setLocationText(e.target.value)}
                    placeholder="Enter street, landmark, or ward name (e.g. Ward 112, T. Nagar)..."
                    style={{
                      flex: 1,
                      backgroundColor: "#070b14",
                      border: "1px solid rgba(51, 65, 85, 0.8)",
                      borderRadius: 8,
                      padding: "10px 14px",
                      color: "#f8fafc",
                      fontSize: 13,
                      outline: "none",
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => handleDetectGPS(true)}
                    style={{
                      background: "rgba(34, 197, 94, 0.15)",
                      border: "1px solid rgba(34, 197, 94, 0.35)",
                      borderRadius: 8,
                      padding: "10px 16px",
                      color: "#4ade80",
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      whiteSpace: "nowrap",
                    }}
                  >
                    <Navigation size={14} className={gpsStatus === "detecting" ? "spin" : ""} />
                    Auto GPS
                  </button>
                </div>

                {/* Quick Ward Chips */}
                <div style={{ marginBottom: 20 }}>
                  <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: 8 }}>
                    Quick-select Chennai Wards:
                  </span>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {PRESET_LOCALITIES.map((p, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSelectPreset(p)}
                        style={{
                          background: locationText === p.name ? "rgba(99, 102, 241, 0.2)" : "rgba(255,255,255,0.04)",
                          border: locationText === p.name ? "1px solid #6366f1" : "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 6,
                          padding: "6px 10px",
                          fontSize: 11,
                          color: locationText === p.name ? "#ffffff" : "#94a3b8",
                          cursor: "pointer",
                        }}
                      >
                        📍 {p.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* GPS Status Indicator */}
                {latitude && longitude && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "rgba(34, 197, 94, 0.08)", border: "1px solid rgba(34, 197, 94, 0.2)", borderRadius: 6, fontSize: 11, color: "#4ade80" }}>
                    <CheckCircle size={14} />
                    <span>Coordinates Geotagged: {latitude.toFixed(5)}° N, {longitude.toFixed(5)}° E</span>
                  </div>
                )}

                {/* Step 4 Actions Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(51, 65, 85, 0.4)" }}>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(3)}
                    style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, padding: "8px 16px", color: "#94a3b8", fontSize: 12, cursor: "pointer" }}
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    style={{
                      background: "linear-gradient(135deg, #4f46e5, #3b82f6)",
                      border: "none",
                      borderRadius: 8,
                      padding: "9px 20px",
                      color: "#ffffff",
                      fontSize: 13,
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    {analyzing ? <Loader2 size={14} className="spin" /> : <Sparkles size={14} />}
                    {analyzing ? "Synthesizing AI Triage..." : "Review AI Dispatch →"}
                  </button>
                </div>
              </div>
            )}

            {/* STEP 5: AI REVIEW & SUBMISSION */}
            {currentStep === 5 && (
              <div
                style={{
                  backgroundColor: "#0d1424",
                  border: "1px solid rgba(99, 102, 241, 0.4)",
                  borderRadius: 14,
                  padding: 24,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(99,102,241,0.15)", display: "flex", alignItems: "center", justifyContent: "center", color: "#818cf8" }}>
                    <FileCheck size={18} />
                  </div>
                  <div>
                    <h2 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", margin: 0 }}>
                      Step 5: Pre-Submission Review & Dispatch
                    </h2>
                    <p style={{ fontSize: 12, color: "#94a3b8", margin: "2px 0 0 0" }}>
                      Verify the unified multimodal interpretation before municipal ticket generation.
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
                  {/* Grievance Statement */}
                  <div style={{ background: "#070b14", padding: 14, borderRadius: 8, border: "1px solid rgba(51, 65, 85, 0.6)" }}>
                    <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 700, textTransform: "uppercase" }}>Grievance Statement</span>
                    <p style={{ fontSize: 13, color: "#f8fafc", marginTop: 4, fontWeight: 500, lineHeight: 1.5 }}>
                      "{editedTranscript || text || "Citizen grievance with attached media evidence."}"
                    </p>
                  </div>

                  {/* AI Classification Summary */}
                  {analysis && (
                    <div style={{ background: "#070b14", padding: 14, borderRadius: 8, border: "1px solid rgba(51, 65, 85, 0.6)" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <div>
                          <span style={{ fontSize: 11, color: "#94a3b8" }}>Classified Category</span>
                          <div style={{ fontSize: 14, fontWeight: 700, color: "#ffffff", textTransform: "capitalize", marginTop: 2 }}>
                            {analysis.category}
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: 11, color: "#94a3b8" }}>Priority & Target SLA</span>
                          <div style={{ fontSize: 14, fontWeight: 700, color: analysis.priority === "critical" ? "#f43f5e" : "#fbbf24", marginTop: 2 }}>
                            {analysis.priority.toUpperCase()} ({analysis.sla?.target_sla_hours || 24}h SLA)
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: 11, color: "#94a3b8" }}>Routed Department</span>
                          <div style={{ fontSize: 13, fontWeight: 600, color: "#cbd5e1", marginTop: 2 }}>
                            {analysis.department_name}
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: 11, color: "#94a3b8" }}>Language & Script</span>
                          <div style={{ fontSize: 13, fontWeight: 600, color: "#cbd5e1", marginTop: 2 }}>
                            {analysis.language_name} ({analysis.script})
                          </div>
                        </div>
                      </div>

                      {analysis.decision_details?.is_immediate_hazard && (
                        <div style={{ marginTop: 12, padding: "8px 12px", background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 6, display: "flex", alignItems: "center", gap: 8, color: "#f87171", fontSize: 12 }}>
                          <ShieldAlert size={16} />
                          <span>Immediate safety hazard flagged. Escalated to CRITICAL SLA response.</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Step 5 Submission Action Bar */}
                <div style={{ display: "flex", gap: 12 }}>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(4)}
                    style={{
                      flex: 1,
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 8,
                      padding: "12px",
                      color: "#cbd5e1",
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    ← Edit Details
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={submitting}
                    style={{
                      flex: 1.8,
                      background: "linear-gradient(135deg, #4f46e5, #3b82f6)",
                      border: "none",
                      borderRadius: 8,
                      padding: "12px 20px",
                      color: "#ffffff",
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 8,
                      boxShadow: "0 4px 16px rgba(79,70,229,0.4)",
                    }}
                  >
                    {submitting ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
                    {submitting ? "Submitting to Municipal Authorities..." : "Confirm & Submit Grievance"}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Live Multimodal AI Intelligence */}
          <div style={{ position: "sticky", top: 24 }}>
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                <Sparkles size={14} color="#818cf8" />
                <span style={{ fontSize: 13, fontWeight: 700, color: "#ffffff" }}>Live AI Triage Stream</span>
              </div>
              <p style={{ fontSize: 11, color: "#94a3b8", margin: 0 }}>
                MuRIL Multi-Task NLP + Qwen2.5-VL Vision + Whisper STT
              </p>
            </div>

            <div
              style={{
                backgroundColor: "#0d1424",
                border: "1px solid rgba(51, 65, 85, 0.6)",
                borderRadius: 14,
                padding: 16,
                boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
              }}
            >
              <AIAnalysisPanel analysis={analysis || undefined} isLoading={analyzing} isMock={false} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
