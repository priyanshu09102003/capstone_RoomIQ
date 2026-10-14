"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { Footer } from "@/components/layout/Footer";
import { SystemBanner } from "@/components/common/SystemBanner";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 antialiased selection:bg-sky-500/20 selection:text-sky-300">
      <SystemBanner />
      <Navbar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 p-4 md:p-8 min-w-0 overflow-y-auto">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  );
}
