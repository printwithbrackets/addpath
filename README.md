# addpath

A lightweight CLI tool for Linux that scans your system for executables not in your `$PATH` and automatically fixes it.

## What it does

Ever downloaded a program and it just... doesn't work in the terminal? `addpath` hunts down executables across your system, detects which ones are missing from your `$PATH`, writes the fix to your shell config, and updates your current session instantly.

## Installation

### Manual

```bash
git clone https://github.com/printwithbrackets/addpath.git
cd addpath
chmod +x install.sh
./install.sh
```

### AUR (coming soon)

```bash
yay -S addpath
```

## Usage

```bash
addpath
```

That's it. It will:

1. Scan common directories for executables
2. Detect which ones are not in your PATH
3. Write the missing export lines to ~/.bashrc and ~/.zshrc
4. Apply the changes to your current session
5. Tell you to run exec $SHELL to fully reload

### Flags

```
--verbose        Show all found executables and their PATH status
--dir <path>     Also scan a custom directory
--scan           Run scan only (default behavior)
```

## Scanned Directories

- ~/.local/bin
- ~/bin
- /opt (recursive, up to 3 levels deep)
- ~/Downloads
- ~/Applications
- ~/.cargo/bin
- ~/.go/bin
- /usr/local/bin
- Flatpak exports
- AppImages in ~ and ~/Downloads

## Requirements

- Python 3
- Linux

## License

MIT - see [LICENSE](LICENSE)
