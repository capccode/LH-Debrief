"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  context: string;
  onContextChange: (context: string) => void;
  outputFolder: string;
  onOutputFolderChange: (folder: string) => void;
}

export default function FileUpload({
  files,
  onFilesChange,
  context,
  onContextChange,
  outputFolder,
  onOutputFolderChange,
}: FileUploadProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      onFilesChange([...files, ...accepted]);
    },
    [files, onFilesChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "audio/*": [],
      "video/*": [],
    },
  });

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
        Input
      </label>

      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
          isDragActive
            ? "border-primary bg-primary/10"
            : "border-slate-600 hover:border-slate-500"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-slate-400">
          {isDragActive ? "Drop files here..." : "Drop audio/video files or click to browse"}
        </p>
      </div>

      {files.length > 0 && (
        <ul className="space-y-1">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="flex items-center justify-between rounded bg-slate-800 px-3 py-1.5 text-sm"
            >
              <span className="truncate text-slate-300">{file.name}</span>
              <button
                onClick={() => removeFile(i)}
                className="ml-2 text-slate-500 hover:text-red-400"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      <div>
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-400">
          Context (-c)
        </label>
        <textarea
          value={context}
          onChange={(e) => onContextChange(e.target.value)}
          placeholder="Optional context for analysis..."
          rows={2}
          className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-400">
          Output Folder
        </label>
        <input
          type="text"
          value={outputFolder}
          onChange={(e) => onOutputFolderChange(e.target.value)}
          placeholder="~/output/"
          className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary focus:outline-none"
        />
      </div>
    </div>
  );
}
