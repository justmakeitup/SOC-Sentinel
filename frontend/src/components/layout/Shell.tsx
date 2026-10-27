import React from "react";
import { AppHeader } from "./AppHeader";
import { Sidebar } from "./Sidebar";

interface ShellProps {
  children: React.ReactNode;
  backendOnline: boolean;
  environment: string;
}

export const Shell: React.FC<ShellProps> = ({
  children,
  backendOnline,
  environment,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F14] text-slate-100 antialiased">
      <AppHeader backendOnline={backendOnline} environment={environment} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6 bg-[#0B0F14]">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
};
