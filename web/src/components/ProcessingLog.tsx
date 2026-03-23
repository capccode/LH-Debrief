"use client";

import { useEffect, useRef } from "react";
import type { LogMessage } from "@/lib/types";

interface ProcessingLogProps {
  logs: LogMessage[];
}

function StatusIcon({ status }: { status: LogMessage["status"] }) {
  switch (status) {
    case "done":
      return <span className="text-green-400">&#10003;</span>;
    case "running":
      return (
        <span className="inline-block text-accent animate-spin">&#10227;</span>
      );
    case "error":
      return <span className="text-red-400">&#10005;</span>;
  }
}

export default function ProcessingLog({ logs }: ProcessingLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="flex flex-col h-full">
      <h3 className="shrink-0 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-700">
        Processing Log
      </h3>
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-sm space-y-1"
      >
        {logs.length === 0 ? (
          <p className="text-slate-600 italic">Waiting for job to start...</p>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="shrink-0 w-4 text-center">
                <StatusIcon status={log.status} />
              </span>
              <span className="text-slate-500 shrink-0">
                [{log.stage}]
              </span>
              <span
                className={
                  log.status === "error" ? "text-red-400" : "text-slate-300"
                }
              >
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
