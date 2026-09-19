"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
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
  Zap,
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
          setLocationText(`GPS Locality (${lat}, ${lng})`);
        }
      },
      (err) => {
        console.warn("GPS access denied or timed out:", err);
        setGpsStatus("denied");
        if (latitude === null) {
          setLatitude(13.0415);
          setLongitude(80.2338);
          if (!locationText) setLocationText("T. Nagar, Chennai");
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
  // Voice Recording Functions
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
          // Convert audio to standard 16kHz PCM WAV for neural Whisper
          let uploadBlob: Blob = rawBlob;
          try {
            uploadBlob = await convertBlobTo16kHzWav(rawBlob);
          } catch (convErr) {
            console.warn("Could not resample in browser, uploading raw blob:", convErr);
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
          console.error("Audio upload/transcription error:", err);
          setTranscriptionError(err.message || "Failed to transcribe audio. Please enter description manually.");
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
      alert("Microphone permission denied or not available in browser.");
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
  // Image Upload Functions
  // ─────────────────────────────────────────────────────────────────────────────
  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setImageError(null);
    const file = e.target.files[0];
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
            observations: ["Photo evidence attached by citizen"],
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
      alert("Please provide a description or voice recording before submitting.");
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

  if (!isMounted) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Loader2 size={32} className="spin" color="var(--accent-indigo)" />
      </div>
    );
  }

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
          background: "var(--brand-navy)",
        }}
      >
        <div
          style={{
            background: "var(--brand-card)",
            border: "1px solid var(--accent-indigo)",
            borderRadius: 16,
            padding: 40,
            maxWidth: 540,
            width: "100%",
            textAlign: "center",
            boxShadow: "0 20px 60px rgba(0,0,0,0.7)",
          }}
        >
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: "50%",
              background: "rgba(34,197,94,0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              boxShadow: "0 0 28px rgba(34,197,94,0.3)",
            }}
          >
            <CheckCircle size={40} color="#22c55e" />
          </div>
          <h2 style={{ marginBottom: 8, fontSize: 24, fontWeight: 800 }}>Grievance Registered</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 20 }}>
            Your multimodal grievance has been authenticated, analyzed by MuRIL AI & Qwen3-VL, and dispatched to the municipal department.
          </p>

          <div
            style={{
              background: "var(--brand-surface)",
              borderRadius: 12,
              padding: 18,
              marginBottom: 24,
              border: "1px solid var(--brand-border)",
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Tracking ID</span>
              <span style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 800, color: "var(--accent-indigo)" }}>
                {complaintCode}
              </span>
            </div>
            {analysis && (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, fontSize: 12 }}>
                  <span style={{ color: "var(--text-muted)" }}>Assigned Department</span>
                  <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{analysis.department_name}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, fontSize: 12 }}>
                  <span style={{ color: "var(--text-muted)" }}>Priority & SLA</span>
                  <span style={{ fontWeight: 700, color: analysis.priority === "critical" ? "#ef4444" : "#f59e0b" }}>
                    {analysis.priority.toUpperCase()} ({analysis.sla?.target_sla_hours || 24} hours)
                  </span>
                </div>
              </>
            )}
            {latitude && longitude && (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12 }}>
                <span style={{ color: "var(--text-muted)" }}>📍 GPS Location</span>
                <span style={{ fontFamily: "monospace", color: "#22c55e" }}>{latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E</span>
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
            <a
              href={`/my-complaints/${complaintCode || complaintId}`}
              className="btn btn-primary"
              style={{ flex: 1, textDecoration: "none", display: "flex", justifyContent: "center", alignItems: "center", gap: 6, fontSize: 13, padding: "12px" }}
            >
              📋 Track My Grievance Status
            </a>
            <a
              href="/map"
              className="btn btn-secondary"
              style={{ flex: 1, textDecoration: "none", display: "flex", justifyContent: "center", alignItems: "center", gap: 6, fontSize: 13, padding: "12px" }}
            >
              🗺️ Live Civic Map
            </a>
          </div>

          <button
            className="btn btn-ghost"
            onClick={() => {
              setSubmitted(false);
              setText("");
              setLocationText("");
              setAnalysis(null);
              resetRecording();
              setImages([]);
              setCurrentStep(1);
            }}
            style={{ width: "100%", fontSize: 12, color: "var(--text-muted)" }}
          >
            + File Another Grievance
          </button>
        </div>
      </div>
    );
  }

  const handleStepClick = (targetStep: number) => {
    if (targetStep < currentStep) {
      setCurrentStep(targetStep);
      return;
    }
    // Allow jumping to Step 2 anytime (citizen can choose to speak)
    if (targetStep === 2) {
      setCurrentStep(2);
      return;
    }
    const hasTextOrVoice = (text && text.trim().length > 0) || (editedTranscript && editedTranscript.trim().length > 0) || !!audioId;
    if (targetStep === 3) {
      if (!hasTextOrVoice) {
        alert("Please provide a text or voice description of your civic issue before proceeding.");
        return;
      }
      setCurrentStep(3);
      return;
    }
    if (targetStep === 4) {
      if (!hasTextOrVoice && images.length === 0) {
        alert("Please provide a text or voice description of your civic issue before setting location.");
        return;
      }
      setCurrentStep(4);
      return;
    }
    if (targetStep === 5) {
      if (!hasTextOrVoice && images.length === 0) {
        alert("Please provide grievance details before reviewing.");
        return;
      }
      handleAnalyze();
    }
  };

  return (
    <div>
      <div className="top-bar">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <h2 style={{ fontSize: 15, fontWeight: 600 }}>Citizen Grievance Submission</h2>
            <span style={{ fontSize: 11, background: "rgba(99,102,241,0.15)", color: "var(--accent-indigo)", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
              Multimodal AI Triage
            </span>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Submit civic grievances using text, voice notes, or photo evidence with instant local AI classification
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 1180, margin: "0 auto", padding: "28px 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.25fr 1fr", gap: 24, alignItems: "start" }}>
          {/* Form side */}
          <div>
            {/* Wizard Steps Bar */}
            <div className="card" style={{ marginBottom: 18, padding: "16px 20px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                {[
                  { step: 1, label: "Describe" },
                  { step: 2, label: "Voice" },
                  { step: 3, label: "Evidence (Optional)" },
                  { step: 4, label: "Location" },
                  { step: 5, label: "AI Review" },
                ].map((s) => {
                  const hasContent = (text && text.trim().length > 0) || (editedTranscript && editedTranscript.trim().length > 0) || !!audioId;
                  const isClickable = s.step <= currentStep || s.step === 2 || (s.step === 3 && hasContent) || (s.step === 4 && hasContent);
                  return (
                    <div
                      key={s.step}
                      onClick={() => handleStepClick(s.step)}
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: 4,
                        cursor: isClickable ? "pointer" : "not-allowed",
                        opacity: currentStep >= s.step ? 1 : isClickable ? 0.75 : 0.35,
                      }}
                    >
                      <div
                        style={{
                          width: 26,
                          height: 26,
                          borderRadius: "50%",
                          background: currentStep === s.step ? "var(--accent-indigo)" : currentStep > s.step ? "#22c55e" : "rgba(255,255,255,0.1)",
                          color: "#fff",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 11,
                          fontWeight: 700,
                          boxShadow: currentStep === s.step ? "0 0 10px rgba(99,102,241,0.5)" : "none",
                        }}
                      >
                        {currentStep > s.step ? "✓" : s.step}
                      </div>
                      <span style={{ fontSize: 11, color: currentStep === s.step ? "var(--text-primary)" : "var(--text-muted)", fontWeight: 600, textAlign: "center" }}>
                        {s.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Step 1: Text Description */}
            {currentStep === 1 && (
              <div className="card" style={{ padding: 20 }}>
                <div style={{ marginBottom: 14 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>
                    Step 1: Describe the Civic Issue
                  </h3>
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Write naturally in Tamil, Tanglish, Hindi, Hinglish, or English. You can also proceed to record a voice note on the next step.
                  </p>
                </div>

                <div style={{ marginBottom: 16 }}>
                  <textarea
                    className="input"
                    value={text}
                    onChange={(e) => {
                      setText(e.target.value);
                      triggerAutoAnalysis(e.target.value);
                    }}
                    placeholder="Describe your issue in Tamil, Tanglish, Hindi, Hinglish, or English (e.g., 'Anna 3 days ah water supply varala', 'Huge pothole on main road')..."
                    style={{ minHeight: 130, fontSize: 13, lineHeight: 1.6, resize: "vertical" }}
                  />
                </div>

                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  {text.trim().length === 0 ? (
                    <>
                      <button onClick={() => setCurrentStep(2)} className="btn btn-secondary" style={{ flex: 1, fontSize: 12, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                        <Mic size={14} color="#ef4444" /> Skip Text & Record Voice Instead →
                      </button>
                      <button
                        onClick={() => {
                          if (!text.trim()) {
                            alert("Please enter a description or click 'Record Voice Instead'.");
                            return;
                          }
                          setCurrentStep(2);
                        }}
                        className="btn btn-primary"
                        style={{ flex: 1, fontSize: 12 }}
                      >
                        Next: Voice Note →
                      </button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => setCurrentStep(2)} className="btn btn-secondary" style={{ flex: 1, fontSize: 12, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                        <Mic size={14} color="var(--accent-indigo)" /> Next: Add Voice Note →
                      </button>
                      <button onClick={() => setCurrentStep(3)} className="btn btn-secondary" style={{ flex: 1, fontSize: 12, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                        <Camera size={14} /> Skip to Photo Evidence →
                      </button>
                      <button onClick={() => setCurrentStep(4)} className="btn btn-primary" style={{ flex: 1, fontSize: 12 }}>
                        Next: Location Tagging →
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Voice Recording (Whisper) */}
            {currentStep === 2 && (
              <div style={{ background: "var(--brand-card)", border: "1px solid var(--brand-border)", borderRadius: 12, padding: 20, marginBottom: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                  <div>
                    <h3 style={{ fontSize: 15, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                      <Mic size={18} color="var(--accent-indigo)" />
                      <span>Step 2: Voice Grievance Recording (Local Whisper STT)</span>
                    </h3>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      Speak naturally in Tamil, Tanglish, Hindi, or English. You can append the transcription to your written text or use it directly.
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 16, margin: "20px 0" }}>
                  {!isRecording ? (
                    <button
                      onClick={startRecording}
                      style={{
                        width: 64,
                        height: 64,
                        borderRadius: "50%",
                        background: "#ef4444",
                        color: "#fff",
                        border: "none",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        boxShadow: "0 0 20px rgba(239,68,68,0.4)",
                      }}
                      title="Click to start recording voice"
                    >
                      <Mic size={28} />
                    </button>
                  ) : (
                    <button
                      onClick={stopRecording}
                      style={{
                        width: 64,
                        height: 64,
                        borderRadius: "50%",
                        background: "#1e293b",
                        border: "2px solid #ef4444",
                        color: "#ef4444",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        animation: "pulse 1.5s infinite",
                      }}
                      title="Click to stop recording"
                    >
                      <Square size={26} fill="#ef4444" />
                    </button>
                  )}

                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "monospace", color: isRecording ? "#ef4444" : "var(--text-primary)" }}>
                      {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, "0")}
                    </div>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {isRecording ? "🔴 Recording live voice... Speak now" : audioBlob ? "Recording ready" : "Tap the red microphone to speak"}
                    </span>
                  </div>
                </div>

                {transcribing && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 12, background: "rgba(99,102,241,0.1)", borderRadius: 8, marginBottom: 14 }}>
                    <Loader2 size={16} className="spin" color="var(--accent-indigo)" />
                    <span style={{ fontSize: 12, color: "var(--accent-indigo)" }}>Running Whisper local speech-to-text recognition...</span>
                  </div>
                )}

                {transcriptionError && (
                  <div style={{ padding: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, color: "#ef4444", fontSize: 12, marginBottom: 14 }}>
                    ⚠ {transcriptionError}
                  </div>
                )}

                {voiceTranscription && (
                  <div style={{ background: "var(--brand-surface)", borderRadius: 10, padding: 14, marginBottom: 14, border: "1px solid var(--brand-border)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "var(--accent-indigo)" }}>
                        🎙 Transcribed ({voiceTranscription.language_name || "Tamil/English"})
                      </span>
                      <button onClick={resetRecording} className="btn-ghost" style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                        <RotateCcw size={12} /> Re-record
                      </button>
                    </div>
                    <textarea
                      className="input"
                      value={editedTranscript}
                      onChange={(e) => {
                        setEditedTranscript(e.target.value);
                        triggerAutoAnalysis(e.target.value);
                      }}
                      style={{ minHeight: 70, fontSize: 13 }}
                      placeholder="Review or edit transcript..."
                    />

                    {/* Quick action buttons for combining text & voice */}
                    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                      {text && text.trim().length > 0 && (
                        <button
                          type="button"
                          onClick={() => {
                            const combined = `${text}\n${editedTranscript}`;
                            setText(combined);
                            triggerAutoAnalysis(combined);
                            alert("Appended voice transcript to your written description.");
                          }}
                          className="btn btn-secondary"
                          style={{ fontSize: 11, padding: "4px 8px" }}
                        >
                          ➕ Append to Written Text
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setText(editedTranscript);
                          triggerAutoAnalysis(editedTranscript);
                        }}
                        className="btn btn-secondary"
                        style={{ fontSize: 11, padding: "4px 8px" }}
                      >
                        🔄 Set as Main Description
                      </button>
                    </div>
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                  <button onClick={() => setCurrentStep(1)} className="btn btn-ghost" style={{ fontSize: 12 }}>
                    ← Back to Description
                  </button>
                  <div style={{ display: "flex", gap: 8 }}>
                    {!voiceTranscription && (
                      <button onClick={() => setCurrentStep(3)} className="btn btn-secondary" style={{ fontSize: 12 }}>
                        Skip Voice →
                      </button>
                    )}
                    <button
                      onClick={() => {
                        if (!text.trim() && !editedTranscript && !audioId) {
                          alert("Please enter a description or record a voice note first.");
                          return;
                        }
                        setCurrentStep(3);
                      }}
                      className="btn btn-primary"
                      style={{ fontSize: 12 }}
                    >
                      Next: Evidence (Optional) →
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Photo Evidence (Optional) */}
            {currentStep === 3 && (
              <div style={{ background: "var(--brand-card)", border: "1px solid var(--brand-border)", borderRadius: 12, padding: 20, marginBottom: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                  <div>
                    <h3 style={{ fontSize: 15, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                      <ImageIcon size={18} color="var(--accent-indigo)" />
                      <span>Step 3: Photo Evidence (Optional Feature)</span>
                    </h3>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      You can optionally attach photos of potholes, fallen wires, waterlogging, or overflowing garbage for grounded AI vision verification.
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
                  <label
                    style={{
                      flex: 1,
                      padding: 24,
                      border: "2px dashed var(--brand-border)",
                      borderRadius: 10,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      background: "rgba(255,255,255,0.02)",
                    }}
                  >
                    <Camera size={28} color="var(--accent-indigo)" style={{ marginBottom: 6 }} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                      {uploadingImage ? "Analyzing with Qwen3-VL..." : "+ Upload Photo Evidence (Optional)"}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                      JPEG, PNG, WebP (up to 15MB)
                    </span>
                    <input type="file" accept="image/*" onChange={handleImageSelect} style={{ display: "none" }} disabled={uploadingImage} />
                  </label>
                </div>

                {imageError && (
                  <div style={{ padding: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, color: "#ef4444", fontSize: 12, marginBottom: 14 }}>
                    ⚠ {imageError}
                  </div>
                )}

                {/* Images List */}
                {images.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
                    {images.map((img, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: "flex",
                          gap: 12,
                          alignItems: "center",
                          background: "var(--brand-surface)",
                          borderRadius: 10,
                          padding: 10,
                          border: "1px solid var(--brand-border)",
                        }}
                      >
                        <img src={img.previewUrl} alt="Evidence" style={{ width: 64, height: 64, objectFit: "cover", borderRadius: 6 }} />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                            <span style={{ fontSize: 11, fontWeight: 700, color: "#fff" }}>
                              {img.analysis?.evidence_category?.replace("_", " ") || "Image Evidence"}
                            </span>
                            <span style={{ fontSize: 10, background: "rgba(99,102,241,0.2)", color: "#818cf8", padding: "1px 6px", borderRadius: 4 }}>
                              {Math.round((img.analysis?.confidence || 0.85) * 100)}% vision conf
                            </span>
                          </div>
                          <p style={{ fontSize: 11, color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
                            {img.analysis?.observations?.[0] || "Visual evidence attached."}
                          </p>
                        </div>
                        <button onClick={() => removeImage(idx)} className="btn-ghost" style={{ color: "#ef4444", padding: 6 }}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <button onClick={() => setCurrentStep(2)} className="btn btn-ghost" style={{ fontSize: 12 }}>
                    ← Back to Voice
                  </button>
                  <button onClick={() => setCurrentStep(4)} className="btn btn-primary" style={{ fontSize: 12 }}>
                    {images.length > 0 ? "Next: Location Tagging →" : "Skip Evidence & Next: Location →"}
                  </button>
                </div>
              </div>
            )}

            {/* Step 4: Location */}
            {currentStep === 4 && (
              <div style={{ background: "var(--brand-card)", border: "1px solid var(--brand-border)", borderRadius: 12, padding: 20, marginBottom: 16 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                  <MapPin size={18} color="var(--accent-indigo)" />
                  <span>Step 4: Location & Spatial Tagging</span>
                </h3>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14 }}>
                  Pinpoint your ward or locality in Chennai for accurate municipal routing.
                </p>

                <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
                  <input
                    className="input"
                    value={locationText}
                    onChange={(e) => setLocationText(e.target.value)}
                    placeholder="e.g. Ward 112, Ranganathan Street, T. Nagar, Chennai"
                    style={{ flex: 1, fontSize: 13 }}
                  />
                  <button
                    onClick={() => handleDetectGPS(true)}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap" }}
                  >
                    <Navigation size={13} className={gpsStatus === "detecting" ? "spin" : ""} />
                    Auto GPS
                  </button>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <button onClick={() => setCurrentStep(3)} className="btn btn-ghost" style={{ fontSize: 12 }}>
                    ← Back to Evidence
                  </button>
                  <button onClick={handleAnalyze} disabled={analyzing} className="btn btn-primary" style={{ fontSize: 12 }}>
                    {analyzing ? <Loader2 size={14} className="spin" /> : <Sparkles size={14} />}
                    {analyzing ? "Analyzing Multimodal Signals..." : "Review AI Understanding →"}
                  </button>
                </div>
              </div>
            )}

            {/* Step 5: AI Understanding Preview & Confirmation */}
            {currentStep === 5 && (
              <div style={{ background: "var(--brand-card)", border: "1px solid var(--accent-indigo)", borderRadius: 12, padding: 20, marginBottom: 16 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                  <FileCheck size={20} color="var(--accent-indigo)" />
                  <span>Step 5: CivicMind AI Pre-Submission Understanding</span>
                </h3>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16 }}>
                  Review the unified interpretation produced by MuRIL v1.1 and Qwen3-VL before dispatch.
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
                  {/* Grievance Statement */}
                  <div style={{ background: "var(--brand-surface)", padding: 14, borderRadius: 8, border: "1px solid var(--brand-border)" }}>
                    <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Grievance Statement</span>
                    <p style={{ fontSize: 13, color: "var(--text-primary)", marginTop: 4, fontWeight: 500, lineHeight: 1.5 }}>
                      "{editedTranscript || text || "Grievance submitted with media evidence."}"
                    </p>
                  </div>

                  {/* AI Understanding Breakdown */}
                  {analysis && (
                    <div style={{ background: "var(--brand-surface)", padding: 14, borderRadius: 8, border: "1px solid var(--brand-border)" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                        <div>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Classified Category</span>
                          <div style={{ fontSize: 14, fontWeight: 700, color: "#fff", textTransform: "capitalize", marginTop: 2 }}>
                            {analysis.category}
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Target Priority & SLA</span>
                          <div style={{ fontSize: 14, fontWeight: 700, color: analysis.priority === "critical" ? "#ef4444" : "#f59e0b", marginTop: 2 }}>
                            {analysis.priority.toUpperCase()} ({analysis.sla?.target_sla_hours || 24}h SLA)
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Routed Department</span>
                          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginTop: 2 }}>
                            {analysis.department_name}
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Detected Language</span>
                          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginTop: 2 }}>
                            {analysis.language_name} ({analysis.script})
                          </div>
                        </div>
                      </div>

                      {analysis.decision_details?.is_immediate_hazard && (
                        <div style={{ padding: "8px 12px", background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 6, display: "flex", alignItems: "center", gap: 8, color: "#ef4444", fontSize: 12 }}>
                          <ShieldAlert size={16} />
                          <span>Immediate safety hazard flagged. Priority escalated to CRITICAL.</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Visual Evidence Summary */}
                  {images.length > 0 && (
                    <div style={{ background: "var(--brand-surface)", padding: 14, borderRadius: 8, border: "1px solid var(--brand-border)" }}>
                      <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Visual Evidence (Qwen3-VL 4B)</span>
                      <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 8 }}>
                        <img src={images[0]?.previewUrl} alt="Evidence" style={{ width: 56, height: 56, objectFit: "cover", borderRadius: 6 }} />
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                            <span style={{ fontSize: 12, fontWeight: 700, color: "#fff" }}>
                              {images[0]?.analysis?.evidence_category}
                            </span>
                            <span style={{ fontSize: 10, background: "rgba(99,102,241,0.2)", color: "#818cf8", padding: "1px 6px", borderRadius: 4 }}>
                              {Math.round((images[0]?.analysis?.confidence || 0.85) * 100)}% conf
                            </span>
                          </div>
                          <p style={{ fontSize: 11, color: "var(--text-secondary)", margin: 0 }}>
                            {images[0]?.analysis?.observations?.[0] || "Visual evidence attached."}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", gap: 10 }}>
                  <button onClick={() => setCurrentStep(4)} className="btn btn-secondary" style={{ flex: 1, fontSize: 13 }}>
                    ← Edit Details
                  </button>
                  <button onClick={handleSubmit} disabled={submitting} className="btn btn-primary" style={{ flex: 1.5, fontSize: 14, padding: "12px" }}>
                    {submitting ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
                    {submitting ? "Submitting to Municipal Authorities..." : "Confirm & Submit Grievance"}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* AI Preview panel side */}
          <div style={{ flex: 1, maxWidth: 420, position: "sticky", top: 24 }}>
            <div style={{ marginBottom: 12 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Live Multimodal Intelligence</h3>
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                MuRIL v1.1 + Qwen3-VL 4B + Local Whisper
              </p>
            </div>
            <AIAnalysisPanel analysis={analysis || undefined} isLoading={analyzing} isMock={false} />
          </div>
        </div>
      </div>
    </div>
  );
}
