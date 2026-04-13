#!/usr/bin/env python3

import os
import sys
import stat
import argparse
from pathlib import Path

BANNER = r"""
  ____  __  ____  _   _    __   ____  ____  ___  ____
 |  _ \ /  ||_   _|| | | |  / /  |  _ \|  _ \| __||  _ \
 | |_) / /\ \ | |  | |_| | / /   | | | | | | | _|  | |_) |
 |____/_/  \_\|_|  |_____||_/    |_| |_|_| |_|___||_|__/

  hunt down executables. own your PATH.
"""

def get_current_path_dirs():
    raw = os.environ.get("PATH", "")
    return set(os.path.realpath(p) for p in raw.split(":") if p)

def is_executable(path: Path) -> bool:
    try:
        st = path.stat()
        return path.is_file() and bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except (PermissionError, OSError):
        return False

def scan_dir(directory: Path, recursive: bool = False, max_depth: int = 1, _depth: int = 0):
    executables = []
    try:
        entries = list(directory.iterdir())
    except (PermissionError, OSError):
        return executables

    for entry in entries:
        try:
            if entry.is_symlink():
                resolved = entry.resolve()
                if resolved.is_file() and is_executable(resolved):
                    executables.append(entry)
            elif entry.is_file():
                if is_executable(entry):
                    executables.append(entry)
            elif entry.is_dir() and recursive and _depth < max_depth:
                executables.extend(
                    scan_dir(entry, recursive=True, max_depth=max_depth, _depth=_depth + 1)
                )
        except (PermissionError, OSError):
            continue

    return executables

def find_appimages(search_dirs):
    appimages = []
    for d in search_dirs:
        p = Path(d).expanduser()
        if not p.exists():
            continue
        try:
            for entry in p.iterdir():
                try:
                    if entry.is_file() and entry.suffix.lower() == ".appimage" and is_executable(entry):
                        appimages.append(entry)
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            continue
    return appimages

def collect_all_executables(extra_dirs=None):
    home = Path.home()

    scan_targets = [
        (home / ".local" / "bin",       False, 1),
        (home / "bin",                   False, 1),
        (Path("/opt"),                   True,  3),
        (home / "Downloads",             False, 1),
        (home / "Applications",          False, 1),
        (home / ".cargo" / "bin",        False, 1),
        (home / ".go" / "bin",           False, 1),
        (Path("/usr/local/bin"),         False, 1),
        (Path("/var/lib/flatpak/exports/bin"),              False, 1),
        (home / ".local/share/flatpak/exports/bin",         False, 1),
    ]

    if extra_dirs:
        for d in extra_dirs:
            scan_targets.append((Path(d).expanduser().resolve(), True, 3))

    executables = []
    for directory, recursive, depth in scan_targets:
        if directory.exists():
            executables.extend(scan_dir(directory, recursive=recursive, max_depth=depth))

    appimage_dirs = [home, home / "Downloads"]
    executables.extend(find_appimages(appimage_dirs))

    return executables

def run(args):
    print(BANNER)

    current_path = get_current_path_dirs()
    executables = collect_all_executables(extra_dirs=args.dir)

    missing_dirs = set()
    found_count = 0

    for exe in executables:
        found_count += 1
        parent = os.path.realpath(exe.parent)

        in_path = parent in current_path

        if args.verbose:
            status = "[IN PATH]" if in_path else "[MISSING]"
            print(f"  {status} {exe}")

        if not in_path:
            missing_dirs.add(parent)

    print()
    print(f"  Executables found : {found_count}")
    print(f"  Dirs not in PATH  : {len(missing_dirs)}")
    print()

    if not missing_dirs:
        print("  All executables are already in PATH.")
    else:
        print("  Add the following to your shell config:\n")
        export_lines = []
        for d in sorted(missing_dirs):
            line = f'export PATH="$PATH:{d}"'
            print(f"    {line}")
            export_lines.append(line)

        if True:
            print()
            shell_configs = [Path.home() / ".bashrc", Path.home() / ".zshrc"]
            wrote_any = False
            for cfg in shell_configs:
                if cfg.exists():
                    # Check if already added to avoid duplicates
                    existing = cfg.read_text()
                    new_lines = [l for l in export_lines if l not in existing]
                    if new_lines:
                        with open(cfg, "a") as f:
                            f.write("\n# Added by pathadder\n")
                            for line in new_lines:
                                f.write(line + "\n")
                        print(f"  [+] Appended to {cfg}")
                        wrote_any = True
                    else:
                        print(f"  [=] {cfg} already up to date")

            # Apply to current process PATH so it takes effect immediately
            current = os.environ.get("PATH", "")
            additions = [str(d) for d in sorted(missing_dirs) if str(d) not in current.split(":")]
            if additions:
                os.environ["PATH"] = current + ":" + ":".join(additions)
                print()
                print("  [+] PATH updated for this session.")

            if wrote_any:
                print()
                print("  To apply changes to your current shell, run:")
                print()
                print("      exec $SHELL")
                print()
                print("  (This restarts your shell in-place — faster than opening a new terminal.)")

    print()

def main():
    parser = argparse.ArgumentParser(
        prog="addpath",
        description="Hunt down executables not in your PATH and fix it."
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan and print results (default behavior)"
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        action="append",
        help="Also scan a custom directory (can be used multiple times)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all found executables and their PATH status"
    )

    args = parser.parse_args()
    run(args)

if __name__ == "__main__":
    main()
