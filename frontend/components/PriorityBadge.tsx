import React from "react";
import { PRIORITIES } from "@/lib/constants";
import type { Priority } from "@/lib/types";

interface PriorityBadgeProps {
  priority: Priority;
  size?: "sm" | "md";
}

const PRIORITY_DOTS: Record<Priority, string> = {
  critical: "●",
  high: "●",
  medium: "●",
  low: "●",
};

export function PriorityBadge({ priority, size = "md" }: PriorityBadgeProps) {
  const config = PRIORITIES[priority];
  return (
    <span
      className={`badge badge-${priority}`}
      style={{ fontSize: size === "sm" ? 10 : 11 }}
    >
      <span style={{ fontSize: 8 }}>{PRIORITY_DOTS[priority]}</span>
      {config.label}
    </span>
  );
}
