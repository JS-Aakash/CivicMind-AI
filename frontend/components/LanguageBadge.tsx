import React from "react";

interface LanguageBadgeProps {
  language?: string;
  languageName?: string;
  script?: string;
  isCodeMixed?: boolean;
  detectedLanguages?: string[];
}

const LANG_COLORS: Record<string, { bg: string; color: string }> = {
  ta: { bg: "rgba(34, 211, 238, 0.12)", color: "#67e8f9" },
  hi: { bg: "rgba(168, 85, 247, 0.12)", color: "#c084fc" },
  en: { bg: "rgba(99, 102, 241, 0.12)", color: "#a5b4fc" },
  te: { bg: "rgba(34, 197, 94, 0.12)", color: "#4ade80" },
  kn: { bg: "rgba(249, 115, 22, 0.12)", color: "#fb923c" },
  default: { bg: "rgba(148, 163, 184, 0.12)", color: "#94a3b8" },
};

const LANG_NAMES: Record<string, string> = {
  ta: "Tamil", hi: "Hindi", en: "English", te: "Telugu",
  kn: "Kannada", ml: "Malayalam", mr: "Marathi", gu: "Gujarati",
  pa: "Punjabi", bn: "Bengali",
};

export function LanguageBadge({
  language,
  languageName,
  script,
  isCodeMixed,
  detectedLanguages,
}: LanguageBadgeProps) {
  const lang = language || "en";
  const style = LANG_COLORS[lang] || LANG_COLORS.default;

  const displayName =
    languageName ||
    (isCodeMixed && detectedLanguages && detectedLanguages.length > 1
      ? detectedLanguages.map((l) => LANG_NAMES[l] || l.toUpperCase()).join(" + ")
      : LANG_NAMES[lang] || lang.toUpperCase());

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "3px 8px",
        borderRadius: 6,
        fontSize: 11,
        fontWeight: 600,
        background: style.bg,
        color: style.color,
        letterSpacing: "0.03em",
      }}
    >
      {displayName}
      {isCodeMixed && (
        <span
          style={{
            fontSize: 9,
            opacity: 0.8,
            background: "rgba(255,255,255,0.1)",
            borderRadius: 4,
            padding: "1px 4px",
          }}
        >
          mixed
        </span>
      )}
      {script && script !== "roman" && !isCodeMixed && (
        <span style={{ fontSize: 9, opacity: 0.7 }}>
          {script === "native" ? "native" : script}
        </span>
      )}
    </span>
  );
}
