"use client";

interface OutputTreeProps {
  files: string[];
  viewingFile: string | null;
  onSelectFile: (filename: string) => void;
}

function fileIcon(filename: string): string {
  if (filename.endsWith(".json")) return "\ud83d\udcca";
  if (filename.endsWith(".md")) return "\ud83d\udcdd";
  return "\ud83d\udcc4";
}

export default function OutputTree({ files, viewingFile, onSelectFile }: OutputTreeProps) {
  return (
    <div className="flex flex-col h-full">
      <h3 className="shrink-0 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-700">
        Output Files
      </h3>
      <div className="flex-1 overflow-y-auto p-2">
        {files.length === 0 ? (
          <p className="p-2 text-sm text-slate-600 italic">
            No output files yet
          </p>
        ) : (
          <ul className="space-y-0.5">
            {files.map((file) => (
              <li key={file}>
                <button
                  onClick={() => onSelectFile(file)}
                  className={`w-full rounded px-2 py-1.5 text-left text-sm transition-colors ${
                    viewingFile === file
                      ? "bg-accent/15 text-accent-light"
                      : "text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  <span className="mr-2">{fileIcon(file)}</span>
                  {file}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
