import React, { useState, useEffect, useRef } from "react";
import { Search, X, ShieldAlert, FolderGit2, Radio, FileCode, ArrowRight } from "lucide-react";
import { NavView } from "../../types";

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (view: NavView) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        if (isOpen) onClose();
      } else if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const quickNavItems: { label: string; view: NavView; icon: React.FC<{ className?: string }>; desc: string }[] = [
    { label: "Overview Dashboard", view: "overview", icon: ShieldAlert, desc: "Operational KPIs, timeseries & alert queues" },
    { label: "Normalized Events", view: "events", icon: Radio, desc: "Unified ECS telemetry logs & ingestion records" },
    { label: "Security Alerts", view: "alerts", icon: ShieldAlert, desc: "Triage queue and deduplicated alarms" },
    { label: "Incident Management", view: "incidents", icon: FolderGit2, desc: "NIST active response cases & evidence notes" },
    { label: "Log Sources & Sensors", view: "sources", icon: Radio, desc: "Syslog, Windows Event & Zeek collectors" },
    { label: "Detection Engineering", view: "rules", icon: FileCode, desc: "MITRE ATT&CK correlation rules & thresholds" },
  ];

  const filteredItems = quickNavItems.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    item.desc.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-20 px-4">
      <div
        className="w-full max-w-xl bg-[#121820] border border-[#1E293B] rounded-lg shadow-2xl overflow-hidden font-mono"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="relative border-b border-[#1E293B] p-3 flex items-center gap-2">
          <Search className="w-4 h-4 text-teal-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a module, rule mnemonic, or command..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Results */}
        <div className="p-2 max-h-80 overflow-y-auto divide-y divide-[#1E293B]">
          <div className="px-3 py-1.5 text-[10px] tracking-wider text-slate-400 uppercase">
            Navigation Targets
          </div>
          {filteredItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.view}
                onClick={() => {
                  onNavigate(item.view);
                  onClose();
                }}
                className="p-2.5 rounded hover:bg-slate-900/60 cursor-pointer flex items-center justify-between group transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-1.5 rounded bg-slate-800 text-teal-400 group-hover:bg-teal-950 transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-200 group-hover:text-teal-300">
                      {item.label}
                    </div>
                    <div className="text-[11px] text-slate-400">{item.desc}</div>
                  </div>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-teal-400 transition-colors" />
              </div>
            );
          })}
        </div>

        {/* Modal Footer Keybindings */}
        <div className="p-2.5 bg-[#0B0F14] border-t border-[#1E293B] text-[10px] text-slate-400 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span>[ESC] to close</span>
            <span>[ENTER] to select</span>
          </div>
          <span className="text-teal-500 font-semibold">Sentinel Command Center</span>
        </div>
      </div>
    </div>
  );
};
