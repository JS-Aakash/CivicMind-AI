import React from "react";
import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface KPICardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  iconColor?: string;
  change?: number;
  changeLabel?: string;
  highlight?: boolean;
}

export function KPICard({
  label,
  value,
  icon: Icon,
  iconColor = "var(--accent-indigo)",
  change,
  changeLabel,
  highlight = false,
}: KPICardProps) {
  const isPositiveChange = change !== undefined && change > 0;
  const isNegativeChange = change !== undefined && change < 0;

  return (
    <div
      className="kpi-card"
      style={
        highlight
          ? { borderColor: "rgba(99,102,241,0.4)", background: "rgba(99,102,241,0.05)" }
          : {}
      }
    >
      {/* Icon */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 10,
          background: `${iconColor}18`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 12,
        }}
      >
        <Icon size={18} color={iconColor} strokeWidth={2} />
      </div>

      {/* Value */}
      <div className="kpi-number">{value}</div>
      <div className="kpi-label">{label}</div>

      {/* Change indicator */}
      {change !== undefined && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            marginTop: 8,
            fontSize: 11,
            color: isPositiveChange
              ? "#f87171"
              : isNegativeChange
              ? "#4ade80"
              : "var(--text-muted)",
          }}
        >
          {isPositiveChange ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
          {Math.abs(change)}% {changeLabel || "vs yesterday"}
        </div>
      )}
    </div>
  );
}
