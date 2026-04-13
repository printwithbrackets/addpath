#!/usr/bin/env python3

import os
import stat
import argparse
from pathlib import Path

BANNER = r"""
  addpath — hunt down executables. own your PATH.
"""

def get_current_path_dirs():
    raw = os.environ.get("PATH", "")
    return set(os.path.realpath(p) for p in raw.split(":") if p)

def is_executable(path: Path) -> bool:
    try:
        st = path.stat()
        return path.is_file() and bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except:
        return False

def scan_dir(directory: Path, recursive=False, max_depth=1, _depth=0):
    executables = []
    try:
        for entry in directory.iterdir():
            if entry.is_file() and is_executable(entry):
                executables.append(entry)
            elif entry.is_dir() and recursive and _depth < max_depth:
                executables.extend(scan_dir(entry, True, max_depth, _depth + 1))
    except:
        pass
    return executables

def collect_all_executables(extra_dirs=None):
    home = Path.home()

    scan_targets = [
        (home / ".local/bin", False, 1),
        (home / "bin", False, 1),
        (Path("/opt"), True, 3),
        (home / "Downloads", False, 1),
        (home / "Applications", False, 1),
        (Path("/usr/local/bin"), False, 1),
    ]

    if extra_dirs:
        for d in extra_dirs:
            scan_targets.append((Path(d).expanduser(), True, 3))

    executables = []
    for directory, recursive, depth in scan_targets:
        if directory.exists():
            executables.extend(scan_dir(directory, recursive, depth))

    return executables

def apply_to_shell_configs(lines):
    shell_configs = [Path.home() / ".bashrc", Path.home() / ".zshrc"]
    wrote = False

    for cfg in shell_configs:
        if cfg.exists():
            content = cfg.read_text()
            new_lines = [l for l in lines if l not in content]

            if new_lines:
                with open(cfg, "a") as f:
                    f.write("\n# added by addpath\n")
                    for l in new_lines:
                        f.write(l + "\n")
                print(f"[+] updated {cfg}")
                wrote = True

    if wrote:
        print("\nrun: exec $SHELL")

def run(args):
    print(BANNER)

    current_path = get_current_path_dirs()
    executables = collect_all_executables(extra_dirs=args.dir)

    missing_dirs = set()

    for exe in executables:
        parent = os.path.realpath(exe.parent)
        if parent not in current_path:
            missing_dirs.add(parent)

    print(f"found executables: {len(executables)}")
    print(f"missing dirs: {len(missing_dirs)}\n")

    if not missing_dirs:
        print("everything already in PATH 👍")
        return

    export_lines = [f'export PATH="$PATH:{d}"' for d in sorted(missing_dirs)]

    print("add these manually:\n")
    for line in export_lines:
        print(" ", line)

    if args.apply:
        print("\napplying changes...\n")
        apply_to_shell_configs(export_lines)

def main():
    parser = argparse.ArgumentParser(description="find executables not in PATH")
    parser.add_argument("--dir", action="append", help="extra directory to scan")
    parser.add_argument("--apply", action="store_true", help="write to shell config")

    args = parser.parse_args()
    run(args)

if __name__ == "__main__":
    main()
