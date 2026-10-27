import React, { useState } from "react";
import {
  Upload,
  X,
  FileText,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { uploadLogFile } from "../../api/sources";
import { IngestionUploadResponse, LogSourceItem } from "../../types";

interface ImportLogModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: () => void;
  sources: LogSourceItem[];
}

export const ImportLogModal: React.FC<ImportLogModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
  sources,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parserType, setParserType] = useState<string>("auto");
  const [selectedSourceId, setSelectedSourceId] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<IngestionUploadResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMessage(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select a file to import.");
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);
    setUploadResult(null);

    try {
      const result = await uploadLogFile(
        selectedFile,
        parserType,
        selectedSourceId || undefined
      );
      setUploadResult(result);
      onImportSuccess();
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to import telemetry file."
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#121820] border border-[#1E293B] rounded-lg max-w-xl w-full p-6 space-y-5 font-mono shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-teal-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              Import Security Logs & Telemetry
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Upload Form or Result View */}
        {!uploadResult ? (
          <div className="space-y-4 text-xs">
            {/* File drop zone / input */}
            <div className="border-2 border-dashed border-[#1E293B] hover:border-teal-700/80 rounded-lg p-5 text-center transition-colors bg-[#0B0F14]">
              <input
                type="file"
                id="log-file-input"
                accept=".csv,.json,.jsonl,.log"
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="log-file-input"
                className="cursor-pointer flex flex-col items-center gap-2"
              >
                <FileText className="w-8 h-8 text-teal-400/80" />
                <div className="text-slate-200 font-semibold">
                  {selectedFile ? selectedFile.name : "Click to select or drag log file"}
                </div>
                <div className="text-[11px] text-slate-400">
                  Accepted formats: CSV, JSON array, NDJSON, LOG (Max 10MB)
                </div>
                {selectedFile && (
                  <div className="text-[10px] text-teal-400">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </div>
                )}
              </label>
            </div>

            {/* Ingestion Parameters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Telemetry Parser
                </label>
                <select
                  value={parserType}
                  onChange={(e) => setParserType(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 text-xs focus:outline-none focus:border-teal-500"
                >
                  <option value="auto">Auto Detect Heuristic</option>
                  <option value="auth">Synthetic Authentication Logs</option>
                  <option value="firewall">Synthetic Firewall / Flow Logs</option>
                  <option value="generic_json">Generic Structured JSON</option>
                  <option value="csv">Standard CSV with Headers</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
                  Log Source Assignment
                </label>
                <select
                  value={selectedSourceId}
                  onChange={(e) => setSelectedSourceId(e.target.value)}
                  className="w-full bg-[#0B0F14] border border-[#1E293B] rounded p-2 text-slate-200 text-xs focus:outline-none focus:border-teal-500"
                >
                  <option value="">Default Feed (Direct-Upload)</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.source_type})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 rounded bg-rose-950/60 border border-rose-800 text-rose-200 flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="text-[11px] leading-relaxed">{errorMessage}</span>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1E293B]">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="px-4 py-1.5 rounded bg-teal-950 hover:bg-teal-900 text-teal-300 border border-teal-800 flex items-center gap-2 font-semibold disabled:opacity-50 transition-colors"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing Ingestion...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-3.5 h-3.5" />
                    <span>Start Ingestion</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Upload Result Report */
          <div className="space-y-4 text-xs">
            {/* Status Headline */}
            <div
              className={`p-4 rounded border flex items-start gap-3 ${
                uploadResult.status === "completed"
                  ? "bg-emerald-950/40 border-emerald-800 text-emerald-200"
                  : uploadResult.status === "partially_failed"
                  ? "bg-amber-950/40 border-amber-800 text-amber-200"
                  : "bg-rose-950/40 border-rose-800 text-rose-200"
              }`}
            >
              {uploadResult.status === "completed" ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : uploadResult.status === "partially_failed" ? (
                <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div>
                <div className="font-bold text-sm uppercase">
                  Ingestion {uploadResult.status.replace("_", " ")}
                </div>
                <p className="mt-1 leading-relaxed text-[11px] opacity-90">
                  {uploadResult.message}
                </p>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-3 gap-2 font-mono text-center">
              <div className="p-2.5 rounded bg-[#0B0F14] border border-[#1E293B]">
                <div className="text-[10px] text-slate-400 uppercase">Normalized</div>
                <div className="text-base font-bold text-emerald-400">
                  {uploadResult.events_processed}
                </div>
              </div>
              <div className="p-2.5 rounded bg-[#0B0F14] border border-[#1E293B]">
                <div className="text-[10px] text-slate-400 uppercase">Quarantined</div>
                <div className="text-base font-bold text-amber-400">
                  {uploadResult.events_failed}
                </div>
              </div>
              <div className="p-2.5 rounded bg-[#0B0F14] border border-[#1E293B]">
                <div className="text-[10px] text-slate-400 uppercase">Volume</div>
                <div className="text-base font-bold text-slate-200">
                  {(uploadResult.bytes_ingested / 1024).toFixed(1)} KB
                </div>
              </div>
            </div>

            {/* Quarantined Records List if partially failed */}
            {uploadResult.rejected_summary && uploadResult.rejected_summary.length > 0 && (
              <div className="space-y-1.5">
                <div className="text-[11px] font-semibold text-amber-300 uppercase flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Quarantined Malformed Rows ({uploadResult.rejected_summary.length})</span>
                </div>
                <div className="max-h-36 overflow-y-auto space-y-1 p-2 bg-[#0B0F14] border border-[#1E293B] rounded text-[11px]">
                  {uploadResult.rejected_summary.map((rej, i) => (
                    <div key={i} className="p-1.5 rounded bg-slate-900 border border-slate-800 space-y-0.5">
                      <div className="text-amber-400 font-bold">
                        Line {rej.line_number}: {rej.reason}
                      </div>
                      {rej.raw_snippet && (
                        <div className="text-slate-400 text-[10px] truncate" title={rej.raw_snippet}>
                          Sample: {rej.raw_snippet}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-3 border-t border-[#1E293B]">
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-1.5 rounded text-slate-300 hover:text-slate-100 bg-slate-800 hover:bg-slate-700 border border-slate-700"
              >
                Import Another File
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-1.5 rounded bg-teal-950 text-teal-300 border border-teal-800 font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
