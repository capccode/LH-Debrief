import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import FileViewer from "../FileViewer";
import { fetchJobOutput } from "@/lib/api";

vi.mock("@/lib/api");

vi.mock("react-markdown", () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>,
}));

vi.mock("remark-gfm", () => ({
  default: () => {},
}));

vi.mock("react-syntax-highlighter", () => ({
  Prism: ({ children }: { children: string }) => (
    <pre data-testid="syntax-highlighter">{children}</pre>
  ),
}));

vi.mock("react-syntax-highlighter/dist/esm/styles/prism", () => ({
  oneDark: {},
}));

describe("FileViewer", () => {
  beforeEach(() => {
    vi.mocked(fetchJobOutput).mockResolvedValue("test content");
  });

  it("shows empty state when no filename", () => {
    render(<FileViewer jobId={null} filename={null} />);
    expect(screen.getByText("Select an output file to view")).toBeInTheDocument();
  });

  it("shows loading state while fetching", () => {
    vi.mocked(fetchJobOutput).mockImplementation(() => new Promise(() => {})); // never resolves
    render(<FileViewer jobId="j1" filename="briefing.md" />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders markdown content for .md files", async () => {
    vi.mocked(fetchJobOutput).mockResolvedValue("# Hello World");
    render(<FileViewer jobId="j1" filename="briefing.md" />);
    await waitFor(() => {
      expect(screen.getByTestId("markdown")).toHaveTextContent("# Hello World");
    });
  });

  it("renders JSON with syntax highlighting for .json files", async () => {
    vi.mocked(fetchJobOutput).mockResolvedValue('{"key": "value"}');
    render(<FileViewer jobId="j1" filename="analysis.json" />);
    await waitFor(() => {
      expect(screen.getByTestId("syntax-highlighter")).toHaveTextContent('{"key": "value"}');
    });
  });

  it("renders plain text for other files", async () => {
    vi.mocked(fetchJobOutput).mockResolvedValue("plain text content");
    render(<FileViewer jobId="j1" filename="transcript.txt" />);
    await waitFor(() => {
      const pre = document.querySelector("pre");
      expect(pre).toBeInTheDocument();
      expect(pre).toHaveTextContent("plain text content");
    });
  });

  it("shows Raw toggle button for .md files", async () => {
    render(<FileViewer jobId="j1" filename="briefing.md" />);
    await waitFor(() => {
      expect(screen.getByText("Raw")).toBeInTheDocument();
    });
  });

  it("Raw toggle switches to raw view", async () => {
    const user = userEvent.setup();
    vi.mocked(fetchJobOutput).mockResolvedValue("# Heading");
    render(<FileViewer jobId="j1" filename="briefing.md" />);
    await waitFor(() => {
      expect(screen.getByTestId("markdown")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Raw"));
    expect(screen.queryByTestId("markdown")).not.toBeInTheDocument();
    expect(screen.getByText("Rendered")).toBeInTheDocument();
  });

  it("does not show Raw toggle for .json files", async () => {
    render(<FileViewer jobId="j1" filename="analysis.json" />);
    await waitFor(() => {
      expect(screen.getByTestId("syntax-highlighter")).toBeInTheDocument();
    });
    expect(screen.queryByText("Raw")).not.toBeInTheDocument();
    expect(screen.queryByText("Rendered")).not.toBeInTheDocument();
  });

  it("shows error on fetch failure", async () => {
    vi.mocked(fetchJobOutput).mockRejectedValue(new Error("fail"));
    render(<FileViewer jobId="j1" filename="briefing.md" />);
    await waitFor(() => {
      expect(screen.getByText("Error loading file")).toBeInTheDocument();
    });
  });

  it("displays filename in header", async () => {
    render(<FileViewer jobId="j1" filename="briefing.md" />);
    await waitFor(() => {
      expect(screen.getByText("briefing.md")).toBeInTheDocument();
    });
  });
});
