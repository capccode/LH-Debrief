"use client";

import { useEffect, useMemo, useReducer } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { fetchJobOutput } from "@/lib/api";

interface FileViewerProps {
  jobId: string | null;
  filename: string | null;
}

type State = { content: string; loading: boolean; showRaw: boolean };
type Action =
  | { type: "fetch_start" }
  | { type: "fetch_done"; content: string }
  | { type: "fetch_error" }
  | { type: "toggle_raw" };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "fetch_start":
      return { ...state, loading: true };
    case "fetch_done":
      return { ...state, loading: false, content: action.content };
    case "fetch_error":
      return { ...state, loading: false, content: "Error loading file" };
    case "toggle_raw":
      return { ...state, showRaw: !state.showRaw };
  }
}

export default function FileViewer({ jobId, filename }: FileViewerProps) {
  const [state, dispatch] = useReducer(reducer, {
    content: "",
    loading: false,
    showRaw: false,
  });

  const shouldFetch = Boolean(jobId && filename);

  useEffect(() => {
    if (!shouldFetch || !jobId || !filename) return;
    let cancelled = false;
    dispatch({ type: "fetch_start" });
    fetchJobOutput(jobId, filename)
      .then((text) => { if (!cancelled) dispatch({ type: "fetch_done", content: text }); })
      .catch(() => { if (!cancelled) dispatch({ type: "fetch_error" }); });
    return () => { cancelled = true; };
  }, [shouldFetch, jobId, filename]);

  const displayContent = useMemo(
    () => (shouldFetch ? state.content : ""),
    [shouldFetch, state.content]
  );

  if (!filename) {
    return (
      <div className="flex h-full items-center justify-center text-slate-600">
        <p>Select an output file to view</p>
      </div>
    );
  }

  if (state.loading) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500">
        <p>Loading...</p>
      </div>
    );
  }

  const isMarkdown = filename.endsWith(".md");
  const isJSON = filename.endsWith(".json");
  const canToggle = isMarkdown;

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="text-sm font-medium text-slate-300">{filename}</span>
        {canToggle && (
          <button
            onClick={() => dispatch({ type: "toggle_raw" })}
            className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            {state.showRaw ? "Rendered" : "Raw"}
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {isMarkdown && !state.showRaw ? (
          <div className="prose-dark">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
          </div>
        ) : isJSON ? (
          <SyntaxHighlighter
            language="json"
            style={oneDark}
            customStyle={{
              background: "transparent",
              margin: 0,
              padding: 0,
              fontSize: "0.875rem",
            }}
          >
            {displayContent}
          </SyntaxHighlighter>
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-sm text-slate-300">
            {displayContent}
          </pre>
        )}
      </div>
    </div>
  );
}
