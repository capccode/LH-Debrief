<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# web/ — Next.js Frontend

Dark-themed dashboard for uploading audio, selecting analysis profiles/blocks/providers, watching live processing logs, and viewing output files.

## Running

```bash
cd web
npm install          # first time
npm run dev          # development (http://localhost:3000)
npm run build        # production build
npm run lint         # ESLint
```

Requires the FastAPI backend running at `http://localhost:8000` (or set `NEXT_PUBLIC_API_URL`).

## Architecture

```
src/
├── app/
│   ├── layout.tsx          # Root layout — dark theme, fonts
│   ├── page.tsx            # Main dashboard — two-panel layout, all state management
│   └── globals.css         # Tailwind directives, scrollbar styles
├── components/
│   ├── FileUpload.tsx      # Drag-drop zone (react-dropzone), file list, context input
│   ├── ProfileSelector.tsx # Dropdown + preview card (name, description, context, blocks)
│   ├── BlockSelector.tsx   # Checkboxes with info tooltips, profile blocks locked
│   ├── ProviderSelector.tsx # Radio (Anthropic/Ollama) + model dropdown
│   ├── ProcessingLog.tsx   # WebSocket log stream with status icons (✓/⟳/✕)
│   ├── OutputTree.tsx      # File tree from job status, click to view
│   └── FileViewer.tsx      # Markdown renderer + JSON highlighter + raw toggle
└── lib/
    ├── api.ts              # Typed fetch functions for all API endpoints + WebSocket
    └── types.ts            # TypeScript interfaces matching API schemas
```

## Design Language

- **Dark theme**: slate-950 background, slate-900 panels, slate-700 borders
- **Colors**: deep purple (`#7c3aed`) primary, cyan (`#06b6d4`) accent
- **Fonts**: Inter (UI), JetBrains Mono (logs, code, transcripts)
- **Layout**: left panel (350px fixed) for controls, right panel (flex-grow) for content

## State Management

All state lives in `page.tsx` via React hooks — no external state library:
- `selectedFiles`, `selectedProfile`, `selectedBlocks`
- `provider`, `model`, `context`
- `currentJobId`, `jobStatus`, `viewingFile`, `logs`

## API Integration

`lib/api.ts` handles all backend communication:
- `fetchProfiles()`, `fetchBlocks()`, `fetchOllamaModels()` — GET endpoints
- `createJob(formData)` — POST multipart upload
- `fetchJobStatus(jobId)`, `fetchJobOutput(jobId, filename)` — polling
- `connectJobLogs(jobId, onMessage)` — WebSocket connection

API base URL: `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost:8000`).

## All components are client components (`"use client"`)

They use browser APIs (WebSocket, File, drag-drop). No server components.

## Key Libraries

| Library | Purpose |
|---------|---------|
| `react-dropzone` | Drag-and-drop file upload |
| `react-markdown` + `remark-gfm` | Render briefing markdown (tables, lists) |
| `react-syntax-highlighter` | JSON syntax highlighting |

## Tailwind CSS v4

This project uses Tailwind v4 — CSS-first configuration. Custom colors and theme extensions are in `globals.css`, not `tailwind.config.ts`.
