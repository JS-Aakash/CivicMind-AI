// CivicMind AI — Utility functions
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncateText(text: string, maxLen = 120): string {
  return text.length > maxLen ? text.slice(0, maxLen) + "…" : text;
}

export function confidencePercent(confidence: number | undefined): string {
  if (confidence === undefined) return "—";
  return `${(confidence * 100).toFixed(1)}%`;
}

export function languageDisplayName(code: string | undefined): string {
  if (!code) return "Unknown";
  const names: Record<string, string> = {
    en: "English", ta: "Tamil", hi: "Hindi", te: "Telugu",
    kn: "Kannada", ml: "Malayalam", mr: "Marathi", gu: "Gujarati",
    pa: "Punjabi", bn: "Bengali",
  };
  return names[code] || code.toUpperCase();
}

export function getPriorityBadgeClass(priority: string): string {
  return `badge badge-${priority}`;
}

export function getStatusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    open: "badge-open",
    in_progress: "badge-in-progress",
    resolved: "badge-resolved",
    pending: "badge badge-medium",
    duplicate: "badge badge-demo",
    closed: "badge",
  };
  return `badge ${map[status] || "badge-open"}`;
}
