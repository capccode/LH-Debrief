import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SettingsModal from "../SettingsModal";
import { fetchSettings, updateSettings } from "@/lib/api";
import { mockSettings } from "@/test/mocks/fixtures";

vi.mock("@/lib/api");

describe("SettingsModal", () => {
  beforeEach(() => {
    vi.mocked(fetchSettings).mockResolvedValue(mockSettings);
    vi.mocked(updateSettings).mockResolvedValue(undefined);
  });

  it("returns null when open=false", () => {
    const { container } = render(<SettingsModal open={false} onClose={vi.fn()} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders modal when open=true", () => {
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("shows status indicators after settings load", async () => {
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    expect(screen.getByText("not set (optional with Ollama)")).toBeInTheDocument();
  });

  it("HF Token field is editable", async () => {
    const user = userEvent.setup();
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    const hfInput = screen.getByPlaceholderText(/leave blank to keep/);
    await user.type(hfInput, "hf_new_token");
    expect(hfInput).toHaveValue("hf_new_token");
  });

  it("Anthropic Key field is editable", async () => {
    const user = userEvent.setup();
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    const keyInput = screen.getByPlaceholderText("sk-ant-...");
    await user.type(keyInput, "sk-test");
    expect(keyInput).toHaveValue("sk-test");
  });

  it("Ollama Host field shows current value after load", async () => {
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      const hostInput = screen.getByDisplayValue("http://localhost:11434");
      expect(hostInput).toBeInTheDocument();
    });
  });

  it("Save button calls updateSettings with entered values", async () => {
    const user = userEvent.setup();
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    const hfInput = screen.getByPlaceholderText(/leave blank to keep/);
    await user.type(hfInput, "hf_new");
    await user.click(screen.getByText("Save"));
    await waitFor(() => {
      expect(updateSettings).toHaveBeenCalledWith(
        expect.objectContaining({ hf_token: "hf_new" })
      );
    });
  });

  it("shows 'Saved' confirmation after save", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    const hfInput = screen.getByPlaceholderText(/leave blank to keep/);
    await user.type(hfInput, "hf_x");
    await user.click(screen.getByText("Save"));
    await waitFor(() => {
      expect(screen.getByText("Saved")).toBeInTheDocument();
    });
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(screen.queryByText("Saved")).not.toBeInTheDocument();
    });
    vi.useRealTimers();
  });

  it("Save button shows 'Saving...' during save", async () => {
    let resolveSave: () => void;
    vi.mocked(updateSettings).mockImplementation(
      () => new Promise((resolve) => { resolveSave = resolve; })
    );
    const user = userEvent.setup();
    render(<SettingsModal open={true} onClose={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText("configured")).toBeInTheDocument();
    });
    const hfInput = screen.getByPlaceholderText(/leave blank to keep/);
    await user.type(hfInput, "hf_x");
    await user.click(screen.getByText("Save"));
    expect(screen.getByText("Saving...")).toBeInTheDocument();
    resolveSave!();
    await waitFor(() => {
      expect(screen.getByText("Save")).toBeInTheDocument();
    });
  });

  it("Cancel button calls onClose", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<SettingsModal open={true} onClose={onClose} />);
    await user.click(screen.getByText("Cancel"));
    expect(onClose).toHaveBeenCalled();
  });

  it("close (X) button calls onClose", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<SettingsModal open={true} onClose={onClose} />);
    await user.click(screen.getByText("×"));
    expect(onClose).toHaveBeenCalled();
  });
});
