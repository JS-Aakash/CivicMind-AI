// CivicMind AI — Constants

export const CATEGORIES = {
  water: { label: "Water", icon: "Droplets", color: "#3b82f6" },
  roads: { label: "Roads", icon: "Construction", color: "#f97316" },
  electricity: { label: "Electricity", icon: "Zap", color: "#eab308" },
  sanitation: { label: "Sanitation", icon: "Trash2", color: "#22c55e" },
  drainage: { label: "Drainage", icon: "CloudRain", color: "#06b6d4" },
  transport: { label: "Transport", icon: "Bus", color: "#8b5cf6" },
  healthcare: { label: "Healthcare", icon: "Heart", color: "#ec4899" },
  public_safety: { label: "Public Safety", icon: "Shield", color: "#ef4444" },
  general: { label: "General", icon: "FileText", color: "#94a3b8" },
} as const;

export const PRIORITIES = {
  critical: { label: "Critical", color: "#ef4444", bg: "rgba(239,68,68,0.15)" },
  high: { label: "High", color: "#f97316", bg: "rgba(249,115,22,0.15)" },
  medium: { label: "Medium", color: "#eab308", bg: "rgba(234,179,8,0.15)" },
  low: { label: "Low", color: "#22c55e", bg: "rgba(34,197,94,0.15)" },
} as const;

export const STATUSES = {
  pending: { label: "Pending", color: "#94a3b8" },
  open: { label: "Open", color: "#6366f1" },
  in_progress: { label: "In Progress", color: "#22d3ee" },
  resolved: { label: "Resolved", color: "#22c55e" },
  closed: { label: "Closed", color: "#475569" },
  duplicate: { label: "Duplicate", color: "#a855f7" },
} as const;

export const LANGUAGES = {
  en: "English",
  ta: "Tamil",
  hi: "Hindi",
  te: "Telugu",
  kn: "Kannada",
  ml: "Malayalam",
  mr: "Marathi",
  gu: "Gujarati",
  pa: "Punjabi",
  bn: "Bengali",
} as const;

export const MAP_CENTER = { lat: 13.0827, lng: 80.2707 }; // Chennai, Tamil Nadu


export const MARKER_COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};

export const DEMO_KPI = {
  total: 4821,
  today: 127,
  high_priority: 43,
  critical: 8,
  ai_confidence: "91.4%",
  open_incidents: 3,
};
