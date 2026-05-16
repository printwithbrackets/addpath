#!/usr/bin/env python3

import os
import re
import stat
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static
from textual import on
from rich.text import Text

# ─── Shell config targets ────────────────────────────────────────────────────

SHELL_CONFIGS = [Path.home() / ".bashrc", Path.home() / ".zshrc"]

SCAN_TARGETS = [
    (Path.home() / ".local/bin",       False, 1),
    (Path.home() / "bin",              False, 1),
    (Path.home() / ".cargo/bin",       False, 1),
    (Path.home() / "go/bin",           False, 1),
    (Path.home() / ".go/bin",          False, 1),
    (Path.home() / "Downloads",        False, 1),
    (Path.home() / "Applications",     False, 1),
    (Path("/opt"),                      True,  3),
    (Path("/usr/local/bin"),            False, 1),
    (Path("/usr/local/go/bin"),         False, 1),
]

# ─── Core logic ──────────────────────────────────────────────────────────────

def get_path_dirs() -> list[str]:
    raw = os.environ.get("PATH", "")
    return [p for p in raw.split(":") if p]


def get_rc_paths() -> set[str]:
    """Return the set of paths explicitly exported in shell configs."""
    rc_paths: set[str] = set()
    pattern = re.compile(
        r'export\s+PATH=["\']?\$PATH:([^"\';\n]+)["\']?'
    )
    for cfg in SHELL_CONFIGS:
        if not cfg.exists():
            continue
        for match in pattern.findall(cfg.read_text()):
            for part in match.split(":"):
                part = part.strip().strip("\"'")
                if part:
                    rc_paths.add(os.path.expanduser(part))
    return rc_paths


def add_to_rc(path_str: str) -> None:
    export_line = f'export PATH="$PATH:{path_str}"'
    for cfg in SHELL_CONFIGS:
        if not cfg.exists():
            continue
        content = cfg.read_text()
        if path_str in content:
            continue
        with open(cfg, "a") as f:
            f.write(f"\n# added by addpath\n{export_line}\n")


def remove_from_rc(path_str: str) -> None:
    for cfg in SHELL_CONFIGS:
        if not cfg.exists():
            continue
        lines = cfg.read_text().splitlines(keepends=True)
        new_lines: list[str] = []
        for line in lines:
            if path_str in line and "PATH" in line:
                # Also strip the preceding addpath comment if present
                if new_lines and new_lines[-1].strip() == "# added by addpath":
                    new_lines.pop()
                continue
            new_lines.append(line)
        cfg.write_text("".join(new_lines))


def is_executable(path: Path) -> bool:
    try:
        st = path.stat()
        return path.is_file() and bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except Exception:
        return False


def scan_dir(directory: Path, recursive: bool = False, max_depth: int = 1, _depth: int = 0) -> list[Path]:
    result: list[Path] = []
    try:
        for entry in directory.iterdir():
            if entry.is_file() and is_executable(entry):
                result.append(entry)
            elif entry.is_dir() and recursive and _depth < max_depth:
                result.extend(scan_dir(entry, True, max_depth, _depth + 1))
    except Exception:
        pass
    return result


def find_missing_dirs() -> list[str]:
    current = {os.path.realpath(p) for p in get_path_dirs()}
    missing: set[str] = set()
    for directory, recursive, depth in SCAN_TARGETS:
        if not directory.exists():
            continue
        for exe in scan_dir(directory, recursive, depth):
            real = os.path.realpath(exe.parent)
            if real not in current:
                missing.add(str(exe.parent))
    return sorted(missing)


# ─── Modals ──────────────────────────────────────────────────────────────────

class AddPathModal(ModalScreen[str | None]):
    CSS = """
    AddPathModal {
        align: center middle;
    }
    #dialog {
        padding: 1 2;
        background: $surface;
        border: double $primary;
        width: 64;
        height: auto;
    }
    #modal_title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    #path_input {
        margin-bottom: 1;
    }
    #btn_row {
        align: right middle;
        height: 3;
    }
    Button { margin-left: 1; }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Add PATH Directory", id="modal_title")
            yield Label("Enter the full path to add:")
            yield Input(placeholder="/path/to/directory", id="path_input")
            with Horizontal(id="btn_row"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Add", variant="primary", id="confirm")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            val = self.query_one("#path_input", Input).value.strip()
            self.dismiss(val or None)

    @on(Button.Pressed, "#confirm")
    def confirm(self) -> None:
        val = self.query_one("#path_input", Input).value.strip()
        self.dismiss(val or None)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class AutoAddModal(ModalScreen[bool]):
    CSS = """
    AutoAddModal {
        align: center middle;
    }
    #dialog {
        padding: 1 2;
        background: $surface;
        border: double $primary;
        width: 72;
        height: auto;
        max-height: 32;
    }
    #modal_title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    #paths_box {
        border: solid $primary-darken-2;
        padding: 0 1;
        height: auto;
        max-height: 16;
        overflow-y: auto;
        margin-bottom: 1;
    }
    #btn_row {
        align: right middle;
        height: 3;
    }
    Button { margin-left: 1; }
    """

    def __init__(self, missing: list[str]) -> None:
        super().__init__()
        self.missing = missing

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Auto Add PATHs", id="modal_title")
            if self.missing:
                yield Label(
                    f"Found [bold]{len(self.missing)}[/bold] director"
                    f"{'y' if len(self.missing) == 1 else 'ies'} with executables not in PATH:",
                    markup=True,
                )
                with ScrollableContainer(id="paths_box"):
                    for p in self.missing:
                        yield Label(f"  [green]+[/green]  {p}", markup=True)
            else:
                yield Label("No missing PATH directories found — everything looks good.")
            with Horizontal(id="btn_row"):
                yield Button("Cancel", variant="default", id="cancel")
                if self.missing:
                    yield Button("Add All", variant="success", id="confirm")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)

    @on(Button.Pressed, "#confirm")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(False)


class ConfirmRemoveModal(ModalScreen[bool]):
    CSS = """
    ConfirmRemoveModal {
        align: center middle;
    }
    #dialog {
        padding: 1 2;
        background: $surface;
        border: double $error;
        width: 64;
        height: auto;
    }
    #modal_title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    #path_label {
        margin-bottom: 1;
        color: $text-muted;
    }
    #btn_row {
        align: right middle;
        height: 3;
    }
    Button { margin-left: 1; }
    """

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Remove PATH Entry", id="modal_title")
            yield Label("This will remove the entry from your session and shell config:")
            yield Label(self.path, id="path_label")
            with Horizontal(id="btn_row"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Remove", variant="error", id="confirm")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)

    @on(Button.Pressed, "#confirm")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(False)


# ─── Main App ─────────────────────────────────────────────────────────────────

class AddPathApp(App):
    TITLE = "addpath"
    SUB_TITLE = "PATH manager"

    CSS = """
    Screen {
        background: $background;
    }

    /* ── Layout ── */
    #main {
        layout: horizontal;
        height: 1fr;
    }

    #left {
        width: 3fr;
        border: solid $primary-darken-2;
        padding: 0;
    }

    #right {
        width: 22;
        border: solid $primary-darken-2;
        padding: 1 1;
        layout: vertical;
    }

    /* ── Panel headers ── */
    .panel-header {
        background: $primary-darken-1;
        color: $text;
        text-style: bold;
        padding: 0 1;
        height: 1;
        width: 100%;
    }

    /* ── Table ── */
    DataTable {
        height: 1fr;
    }

    /* ── Sidebar buttons ── */
    #right Label.section-label {
        color: $text-muted;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }

    /* ── Legend ── */
    #legend {
        margin-top: 1;
        border: solid $primary-darken-2;
        padding: 1;
        height: auto;
    }

    #legend Label {
        height: 1;
    }

    /* ── Status bar ── */
    #status {
        height: 1;
        background: $primary-darken-2;
        color: $text-muted;
        padding: 0 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("a", "add_path", "Add"),
        Binding("d", "remove_path", "Remove"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    # ── Setup ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main"):
            with Vertical(id="left"):
                yield Label(" PATH Entries", classes="panel-header")
                yield DataTable(id="path_table", cursor_type="row")
            with Vertical(id="right"):
                yield Label("Scan", classes="section-label")
                yield Button("Auto Add PATHs", id="btn_auto", variant="success")
                yield Label("Manage", classes="section-label")
                yield Button("Add PATH", id="btn_add", variant="primary")
                yield Button("Remove Selected", id="btn_remove", variant="error")
                yield Button("Refresh", id="btn_refresh", variant="default")
                with Container(id="legend"):
                    yield Label("[green]●[/] Persistent", markup=True)
                    yield Label("[yellow]●[/] Session only", markup=True)
                    yield Label("[red]●[/] Dir missing", markup=True)
        yield Label(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._load_table()
        self._set_status("Ready  —  [bold]a[/] add  [bold]d[/] remove  [bold]r[/] refresh  [bold]q[/] quit", markup=True)

    # ── Table ──────────────────────────────────────────────────────────────

    def _load_table(self) -> None:
        table = self.query_one("#path_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Directory", "On Disk")

        current = get_path_dirs()
        rc = get_rc_paths()

        for p in current:
            expanded = os.path.expanduser(p)
            exists = Path(expanded).exists()
            in_rc = expanded in rc or p in rc

            if not exists:
                status = Text("● Missing",    style="bold red")
            elif in_rc:
                status = Text("● Persistent", style="bold green")
            else:
                status = Text("● Session",    style="bold yellow")

            on_disk = Text("yes", style="green") if exists else Text("no", style="red")
            table.add_row(status, p, on_disk)

    def _set_status(self, msg: str, markup: bool = False) -> None:
        bar = self.query_one("#status", Label)
        if markup:
            bar.update(msg)
        else:
            bar.update(msg)

    def _selected_path(self) -> str | None:
        table = self.query_one("#path_table", DataTable)
        if table.cursor_row is None:
            return None
        try:
            row = table.get_row_at(table.cursor_row)
            return str(row[1])
        except Exception:
            return None

    # ── Button handlers ────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn_auto")
    def handle_auto(self) -> None:
        self._set_status("Scanning for missing executables...")
        missing = find_missing_dirs()

        def done(confirmed: bool) -> None:
            if confirmed and missing:
                for p in missing:
                    add_to_rc(p)
                    current = os.environ.get("PATH", "")
                    if p not in current:
                        os.environ["PATH"] = current + ":" + p
                self._load_table()
                self._set_status(f"Added {len(missing)} director{'y' if len(missing) == 1 else 'ies'} to PATH and shell config.")
            elif not missing:
                self._set_status("Scan complete — no missing directories found.")
            else:
                self._set_status("Cancelled.")

        self.push_screen(AutoAddModal(missing), done)

    @on(Button.Pressed, "#btn_add")
    def handle_add(self) -> None:
        def done(path: str | None) -> None:
            if path:
                add_to_rc(path)
                current = os.environ.get("PATH", "")
                if path not in current:
                    os.environ["PATH"] = current + ":" + path
                self._load_table()
                self._set_status(f"Added: {path}")
            else:
                self._set_status("Cancelled.")

        self.push_screen(AddPathModal(), done)

    @on(Button.Pressed, "#btn_remove")
    def handle_remove(self) -> None:
        path = self._selected_path()
        if not path:
            self._set_status("No entry selected. Use arrow keys to select a row.")
            return

        def done(confirmed: bool) -> None:
            if confirmed:
                remove_from_rc(path)
                current = get_path_dirs()
                os.environ["PATH"] = ":".join(p for p in current if p != path)
                self._load_table()
                self._set_status(f"Removed: {path}")
            else:
                self._set_status("Cancelled.")

        self.push_screen(ConfirmRemoveModal(path), done)

    @on(Button.Pressed, "#btn_refresh")
    def handle_refresh(self) -> None:
        self._load_table()
        self._set_status("Refreshed.")

    # ── Keyboard actions ───────────────────────────────────────────────────

    def action_add_path(self) -> None:
        self.handle_add()

    def action_remove_path(self) -> None:
        self.handle_remove()

    def action_refresh(self) -> None:
        self.handle_refresh()


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    AddPathApp().run()


if __name__ == "__main__":
    main()
