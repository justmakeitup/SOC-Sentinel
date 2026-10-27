import React, { useState } from "react";
import { AppHeader } from "./AppHeader";
import { Sidebar } from "./Sidebar";
import { GlobalSearchModal } from "./GlobalSearchModal";
import { DemoDataBanner } from "../common/DemoDataBanner";
import { NavView } from "../../types";

interface ShellProps {
  children: React.ReactNode;
  backendOnline: boolean;
  environment: string;
  latencyMs?: number | null;
  demoMode: boolean;
  onToggleDemoMode: () => void;
  currentView: NavView;
  onNavigate: (view: NavView) => void;
}

export const Shell: React.FC<ShellProps> = ({
  children,
  backendOnline,
  environment,
  latencyMs,
  demoMode,
  onToggleDemoMode,
  currentView,
  onNavigate,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F14] text-slate-100 antialiased selection:bg-teal-900 selection:text-teal-200">
      {/* Top Navigation Bar */}
      <AppHeader
        backendOnline={backendOnline}
        environment={environment}
        latencyMs={latencyMs}
        demoMode={demoMode}
        onToggleDemoMode={onToggleDemoMode}
        onOpenSearch={() => setSearchModalOpen(true)}
        onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)}
      />

      {/* Main Layout Container */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Desktop Collapsible Sidebar */}
        <div className="hidden md:flex shrink-0">
          <Sidebar
            currentView={currentView}
            onNavigate={onNavigate}
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
          />
        </div>

        {/* Mobile Drawer Sidebar */}
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-40 md:hidden flex">
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setMobileSidebarOpen(false)}
            />
            <div className="relative w-64 max-w-[80%] bg-[#0E141D] z-50 h-full flex flex-col">
              <Sidebar
                currentView={currentView}
                onNavigate={(v) => {
                  onNavigate(v);
                  setMobileSidebarOpen(false);
                }}
                collapsed={false}
                onToggleCollapse={() => setMobileSidebarOpen(false)}
              />
            </div>
          </div>
        )}

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#0B0F14]">
          <div className="max-w-7xl mx-auto space-y-6">
            {demoMode && <DemoDataBanner onDisable={onToggleDemoMode} />}
            {children}
          </div>
        </main>
      </div>

      {/* Global Command Palette / Search Modal */}
      <GlobalSearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        onNavigate={onNavigate}
      />
    </div>
  );
};
