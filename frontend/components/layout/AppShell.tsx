"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { isAuthenticated } from "@/lib/auth";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  const isCitizenPage =
    pathname === "/" ||
    pathname.startsWith("/report") ||
    pathname.startsWith("/track") ||
    pathname.startsWith("/admin/login");

  // Protection for admin pages
  useEffect(() => {
    if (!isCitizenPage) {
      if (!isAuthenticated()) {
        router.push("/admin/login");
      }
    }
  }, [pathname, isCitizenPage, router]);

  if (isCitizenPage) {
    return <main className="main-content citizen-layout" style={{ marginLeft: 0, width: "100%" }}>{children}</main>;
  }

  return (
    <div className="app-shell flex min-h-screen">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <main
        className="main-content flex-1"
        style={{
          marginLeft: collapsed ? "var(--sidebar-collapsed-width, 64px)" : "var(--sidebar-width, 240px)",
          minHeight: "100vh",
          transition: "margin-left 0.25s ease",
          background: "var(--brand-navy)",
        }}
      >
        {children}
      </main>
    </div>
  );
}
