"use client";

import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import type { Profile, JobStatus, LogMessage } from "@/lib/types";
import { createJob, fetchJobStatus, connectJobLogs } from "@/lib/api";
import FileUpload from "@/components/FileUpload";
import ProfileSelector from "@/components/ProfileSelector";
import BlockSelector from "@/components/BlockSelector";
import ProviderSelector from "@/components/ProviderSelector";
import ProcessingLog from "@/components/ProcessingLog";
import OutputTree from "@/components/OutputTree";
import FileViewer from "@/components/FileViewer";

export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [selectedBlocks, setSelectedBlocks] = useState<string[]>([]);
  const [provider, setProvider] = useState<"anthropic" | "ollama">("ollama");
  const [model, setModel] = useState("");
  const [context, setContext] = useState("");
  const [outputFolder, setOutputFolder] = useState("");
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [viewingFile, setViewingFile] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const profileBlocks = useMemo(
    () => selectedProfile?.blocks ?? [],
    [selectedProfile]
  );
  const hasFiles = selectedFiles.length > 0;
  const hasBlocks = profileBlocks.length > 0 || selectedBlocks.length > 0;
  const isRunning = jobStatus?.status === "queued" || jobStatus?.status === "processing";
  const canRun = hasFiles && hasBlocks && !isRunning && !isSubmitting;

  // Poll job status
  useEffect(() => {
    if (!currentJobId) return;

    const poll = () => {
      fetchJobStatus(currentJobId).then((status) => {
        setJobStatus(status);
        if (status.status === "completed" || status.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      });
    };

    poll();
    pollRef.current = setInterval(poll, 2000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [currentJobId]);

  // WebSocket for logs
  useEffect(() => {
    if (!currentJobId) return;

    wsRef.current = connectJobLogs(currentJobId, (msg) => {
      setLogs((prev) => [...prev, msg]);
    });

    return () => {
      wsRef.current?.close();
    };
  }, [currentJobId]);

  const handleRun = useCallback(async () => {
    if (!canRun || selectedFiles.length === 0) return;

    setIsSubmitting(true);
    setLogs([]);
    setJobStatus(null);
    setViewingFile(null);

    const formData = new FormData();
    formData.append("file", selectedFiles[0]);
    if (selectedProfile) formData.append("profile", selectedProfile.id);

    const allBlocks = [...profileBlocks, ...selectedBlocks];
    allBlocks.forEach((b) => formData.append("blocks", b));

    formData.append("provider", provider);
    if (model) formData.append("model", model);
    if (context) formData.append("context", context);
    if (outputFolder) formData.append("output_folder", outputFolder);

    try {
      const { job_id } = await createJob(formData);
      setCurrentJobId(job_id);
    } catch {
      setLogs([
        {
          timestamp: new Date().toISOString(),
          stage: "submit",
          message: "Failed to create job",
          status: "error",
        },
      ]);
    } finally {
      setIsSubmitting(false);
    }
  }, [canRun, selectedFiles, selectedProfile, profileBlocks, selectedBlocks, provider, model, context, outputFolder]);

  return (
    <div className="flex h-screen flex-col">
      {/* Header — draggable titlebar region for Electron */}
      <header
        className="shrink-0 border-b border-slate-800 px-6 py-3 text-center"
        style={{ WebkitAppRegion: "drag" } as React.CSSProperties}
      >
        <h1 className="text-lg font-semibold text-slate-100 tracking-tight">
          LH-Debrief
        </h1>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — controls */}
        <aside className="w-[350px] shrink-0 overflow-y-auto border-r border-slate-800 bg-slate-900 p-4 space-y-6">
          <FileUpload
            files={selectedFiles}
            onFilesChange={setSelectedFiles}
            context={context}
            onContextChange={setContext}
            outputFolder={outputFolder}
            onOutputFolderChange={setOutputFolder}
          />

          <ProfileSelector
            selected={selectedProfile}
            onSelect={setSelectedProfile}
          />

          <BlockSelector
            selectedBlocks={selectedBlocks}
            onBlocksChange={setSelectedBlocks}
            profileBlocks={profileBlocks}
          />

          <ProviderSelector
            provider={provider}
            onProviderChange={setProvider}
            model={model}
            onModelChange={setModel}
          />

          <button
            onClick={handleRun}
            disabled={!canRun}
            className={`w-full rounded-lg py-2.5 text-sm font-semibold transition-colors ${
              canRun
                ? "bg-primary text-white hover:bg-primary-dark"
                : "bg-slate-800 text-slate-600 cursor-not-allowed"
            }`}
          >
            {isRunning
              ? "Processing..."
              : isSubmitting
              ? "Submitting..."
              : "\u25b6 Run Analysis"}
          </button>
        </aside>

        {/* Right panel — content */}
        <main className="flex flex-1 flex-col overflow-hidden">
          {/* File viewer (top) */}
          <div className="flex-1 overflow-hidden border-b border-slate-800">
            <FileViewer jobId={currentJobId} filename={viewingFile} />
          </div>

          {/* Bottom split: log + output tree */}
          <div className="flex h-64 shrink-0">
            <div className="flex-1 overflow-hidden border-r border-slate-800">
              <ProcessingLog logs={logs} />
            </div>
            <div className="w-72 shrink-0 overflow-hidden">
              <OutputTree
                files={jobStatus?.files ?? []}
                viewingFile={viewingFile}
                onSelectFile={setViewingFile}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
