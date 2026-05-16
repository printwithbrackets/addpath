# addpath

A TUI PATH manager for Linux. Scan your system for executables not in `$PATH`, add missing directories interactively, and remove stale entries — all from a clean terminal interface.

## What it does

- Shows all current `$PATH` entries with their status (persistent, session-only, or missing on disk)
- Auto-scans common locations for executables and offers to add missing directories
- Add or remove PATH entries interactively
- Writes changes to `~/.bashrc` and `~/.zshrc` automatically

## Installation

### AUR

```bash
yay -S addpath
```

### Manual

```bash
pip install textual
install -Dm755 addpath.py ~/.local/bin/addpath
```

## Usage

```bash
addpath
```

### Key bindings

| Key | Action |
|-----|--------|
| `a` | Add a PATH entry manually |
| `d` | Remove the selected entry |
| `r` | Refresh the table |
| `q` | Quit |

### Buttons

- **Auto Add PATHs** — scans common directories for executables not in PATH and lets you add them all at once
- **Add PATH** — opens a prompt to type a directory path manually
- **Remove Selected** — removes the highlighted entry from your session and shell config

## Path status indicators

| Color | Meaning |
|-------|---------|
| Green ● Persistent | Found in `~/.bashrc` or `~/.zshrc` — survives reboots |
| Yellow ● Session | In current `$PATH` but not in any shell config |
| Red ● Missing | In `$PATH` but the directory doesn't exist on disk |

## Scanned Directories (Auto Add)

- `~/.local/bin`
- `~/bin`
- `~/.cargo/bin`
- `~/go/bin` / `~/.go/bin`
- `~/Downloads`
- `~/Applications`
- `/opt` (recursive, up to 3 levels)
- `/usr/local/bin`
- `/usr/local/go/bin`

## Requirements

- Python 3.10+
- [textual](https://github.com/Textualize/textual) (`pip install textual` or `python-textual` on AUR)
- Linux

## License

MIT — see [LICENSE](LICENSE)
