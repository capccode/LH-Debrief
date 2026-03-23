import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import FileUpload from "../FileUpload";
import { browseFolder } from "@/lib/api";
import { createMockFile } from "@/test/mocks/fixtures";

vi.mock("@/lib/api");

const defaultProps = {
  files: [] as File[],
  onFilesChange: vi.fn(),
  context: "",
  onContextChange: vi.fn(),
  outputFolder: "",
  onOutputFolderChange: vi.fn(),
};

describe("FileUpload", () => {
  beforeEach(() => {
    vi.mocked(browseFolder).mockResolvedValue("/selected/path");
  });

  it("renders drop zone with prompt text", () => {
    render(<FileUpload {...defaultProps} />);
    expect(screen.getByText("Drop audio/video files or click to browse")).toBeInTheDocument();
  });

  it("shows file list when files are provided", () => {
    const files = [createMockFile("test.wav"), createMockFile("interview.mp3", "audio/mpeg")];
    render(<FileUpload {...defaultProps} files={files} />);
    expect(screen.getByText("test.wav")).toBeInTheDocument();
    expect(screen.getByText("interview.mp3")).toBeInTheDocument();
  });

  it("remove button calls onFilesChange without removed file", async () => {
    const user = userEvent.setup();
    const files = [createMockFile("a.wav"), createMockFile("b.wav")];
    const onFilesChange = vi.fn();
    render(<FileUpload {...defaultProps} files={files} onFilesChange={onFilesChange} />);
    const removeButtons = screen.getAllByText("✕");
    await user.click(removeButtons[0]);
    expect(onFilesChange).toHaveBeenCalledWith([files[1]]);
  });

  it("context textarea reflects value", () => {
    render(<FileUpload {...defaultProps} context="test context" />);
    const textarea = screen.getByPlaceholderText("Optional context for analysis...");
    expect(textarea).toHaveValue("test context");
  });

  it("context textarea calls onContextChange", async () => {
    const user = userEvent.setup();
    const onContextChange = vi.fn();
    render(<FileUpload {...defaultProps} onContextChange={onContextChange} />);
    const textarea = screen.getByPlaceholderText("Optional context for analysis...");
    await user.type(textarea, "a");
    expect(onContextChange).toHaveBeenCalledWith("a");
  });

  it("output folder input reflects value", () => {
    render(<FileUpload {...defaultProps} outputFolder="/my/output" />);
    const input = screen.getByPlaceholderText("~/output/");
    expect(input).toHaveValue("/my/output");
  });

  it("output folder input calls onOutputFolderChange", async () => {
    const user = userEvent.setup();
    const onOutputFolderChange = vi.fn();
    render(<FileUpload {...defaultProps} onOutputFolderChange={onOutputFolderChange} />);
    const input = screen.getByPlaceholderText("~/output/");
    await user.type(input, "x");
    expect(onOutputFolderChange).toHaveBeenCalled();
  });

  it("Browse button calls browseFolder API and updates folder", async () => {
    const user = userEvent.setup();
    const onOutputFolderChange = vi.fn();
    render(<FileUpload {...defaultProps} onOutputFolderChange={onOutputFolderChange} />);
    await user.click(screen.getByTitle("Browse for folder"));
    await waitFor(() => {
      expect(onOutputFolderChange).toHaveBeenCalledWith("/selected/path");
    });
  });

  it("Browse button shows loading state while picking", async () => {
    let resolveBrowse: (val: string) => void;
    vi.mocked(browseFolder).mockImplementation(
      () => new Promise((resolve) => { resolveBrowse = resolve; })
    );
    const user = userEvent.setup();
    render(<FileUpload {...defaultProps} />);
    const browseButton = screen.getByTitle("Browse for folder");
    expect(browseButton).toHaveTextContent("Browse");
    await user.click(browseButton);
    expect(browseButton).toHaveTextContent("...");
    resolveBrowse!("/path");
    await waitFor(() => {
      expect(browseButton).toHaveTextContent("Browse");
    });
  });
});
