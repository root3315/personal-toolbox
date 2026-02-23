#!/usr/bin/env python3
"""
personal-toolbox: A collection of daily utility scripts and helpers.
Provides file management, system monitoring, text processing, and network tools.
"""

import os
import sys
import json
import gzip
import shutil
import hashlib
import argparse
import datetime
import subprocess
import socket
from pathlib import Path
from collections import Counter


def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def disk_usage_summary(path="."):
    """Return disk usage summary for the given path."""
    try:
        usage = shutil.disk_usage(path)
        return {
            "total": format_size(usage.total),
            "used": format_size(usage.used),
            "free": format_size(usage.free),
            "percent_used": round(usage.used / usage.total * 100, 1),
        }
    except OSError as e:
        return {"error": str(e)}


def find_large_files(directory, min_size_mb=100):
    """Find files larger than min_size_mb in the given directory."""
    large_files = []
    min_bytes = min_size_mb * 1024 * 1024
    for root, _, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                if os.path.isfile(filepath) and not os.path.islink(filepath):
                    size = os.path.getsize(filepath)
                    if size >= min_bytes:
                        large_files.append({"path": filepath, "size": format_size(size)})
            except OSError:
                continue
    return sorted(large_files, key=lambda x: x["path"])


def compute_file_hash(filepath, algorithm="sha256"):
    """Compute hash of a file using the specified algorithm."""
    h = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compress_file(input_path, output_path=None):
    """Compress a file using gzip."""
    if output_path is None:
        output_path = str(input_path) + ".gz"
    with open(input_path, "rb") as f_in:
        with gzip.open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    original_size = os.path.getsize(input_path)
    compressed_size = os.path.getsize(output_path)
    ratio = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0
    return {
        "original": format_size(original_size),
        "compressed": format_size(compressed_size),
        "reduction_percent": ratio,
    }


def decompress_file(gz_path, output_path=None):
    """Decompress a gzip file."""
    if output_path is None:
        output_path = gz_path.replace(".gz", "")
    with gzip.open(gz_path, "rb") as f_in:
        with open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    return output_path


def count_lines_in_file(filepath):
    """Count the number of lines in a text file."""
    count = 0
    with open(filepath, "r", errors="ignore") as f:
        for line in f:
            count += 1
    return count


def find_duplicate_files(directory):
    """Find duplicate files in a directory based on content hash."""
    hash_map = {}
    for root, _, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                if os.path.isfile(filepath):
                    file_hash = compute_file_hash(filepath)
                    if file_hash not in hash_map:
                        hash_map[file_hash] = []
                    hash_map[file_hash].append(filepath)
            except (OSError, PermissionError):
                continue
    return {h: paths for h, paths in hash_map.items() if len(paths) > 1}


def get_recent_files(directory, days=7):
    """List files modified in the last N days."""
    recent = []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    for root, _, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime >= cutoff:
                    recent.append({
                        "path": filepath,
                        "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                        "size": format_size(os.path.getsize(filepath)),
                    })
            except OSError:
                continue
    return sorted(recent, key=lambda x: x["modified"], reverse=True)


def word_frequency(text, top_n=10):
    """Return the top N most frequent words in text."""
    words = text.lower().split()
    cleaned = [w.strip(".,!?;:\"'()[]{}") for w in words if len(w.strip(".,!?;:\"'()[]{}")) > 2]
    return Counter(cleaned).most_common(top_n)


def search_and_replace_in_file(filepath, search, replace, dry_run=False):
    """Search and replace text in a file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    occurrences = content.count(search)
    if occurrences == 0:
        return {"filepath": filepath, "occurrences": 0, "modified": False}
    if dry_run:
        return {"filepath": filepath, "occurrences": occurrences, "modified": False}
    new_content = content.replace(search, replace)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return {"filepath": filepath, "occurrences": occurrences, "modified": True}


def check_port_open(host, port, timeout=2):
    """Check if a TCP port is open on a host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, OSError):
        return False


def get_system_uptime():
    """Get system uptime from /proc/uptime."""
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.read().split()[0])
        delta = datetime.timedelta(seconds=int(seconds))
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m"
    except (OSError, ValueError):
        return "unknown"


def get_cpu_count():
    """Return the number of CPU cores."""
    return os.cpu_count() or 1


def get_memory_info():
    """Read memory info from /proc/meminfo on Linux."""
    info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                value_kb = int(parts[1])
                info[key] = format_size(value_kb * 1024)
        return {
            "total": info.get("MemTotal", "unknown"),
            "available": info.get("MemAvailable", info.get("MemFree", "unknown")),
        }
    except (OSError, ValueError, IndexError):
        return {"error": "unable to read memory info"}


def generate_password(length=16, use_symbols=True, use_upper=True):
    """Generate a random password."""
    import secrets
    charset = "abcdefghijklmnopqrstuvwxyz"
    if use_upper:
        charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    charset += "0123456789"
    if use_symbols:
        charset += "!@#$%^&*()-_=+"
    password = "".join(secrets.choice(charset) for _ in range(length))
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not has_upper and use_upper:
        pos = secrets.randbelow(length)
        password = password[:pos] + secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + password[pos + 1:]
    if not has_digit:
        pos = secrets.randbelow(length)
        password = password[:pos] + secrets.choice("0123456789") + password[pos + 1:]
    return password


def cleanup_old_files(directory, max_age_days=30):
    """Delete files older than max_age_days."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
    deleted = []
    for root, _, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    deleted.append(filepath)
            except OSError:
                continue
    return deleted


def cmd_system_info(args):
    """Display system information."""
    print(f"Hostname: {socket.gethostname()}")
    print(f"Uptime: {get_system_uptime()}")
    print(f"CPU cores: {get_cpu_count()}")
    mem = get_memory_info()
    print(f"Memory total: {mem.get('total', 'N/A')}")
    print(f"Memory available: {mem.get('available', 'N/A')}")
    disk = disk_usage_summary(args.path)
    print(f"Disk ({args.path}):")
    for key, val in disk.items():
        print(f"  {key}: {val}")


def cmd_find_large(args):
    """Find large files."""
    results = find_large_files(args.directory, args.min_size)
    if not results:
        print(f"No files found larger than {args.min_size}MB")
        return
    for item in results:
        print(f"{item['size']:>12}  {item['path']}")


def cmd_duplicates(args):
    """Find duplicate files."""
    dupes = find_duplicate_files(args.directory)
    if not dupes:
        print("No duplicates found.")
        return
    for hash_val, paths in dupes.items():
        print(f"\nDuplicate set (hash: {hash_val[:12]}...):")
        for p in paths:
            size = format_size(os.path.getsize(p))
            print(f"  {size:>10}  {p}")


def cmd_hash(args):
    """Compute file hash."""
    for filepath in args.files:
        if os.path.isfile(filepath):
            h = compute_file_hash(filepath, args.algorithm)
            print(f"{h}  {filepath}")
        else:
            print(f"File not found: {filepath}", file=sys.stderr)


def cmd_compress(args):
    """Compress a file."""
    result = compress_file(args.input, args.output)
    print(f"Compressed: {args.input}")
    print(f"  Original: {result['original']}")
    print(f"  Compressed: {result['compressed']}")
    print(f"  Reduction: {result['reduction_percent']}%")


def cmd_recent(args):
    """Show recently modified files."""
    results = get_recent_files(args.directory, args.days)
    if not results:
        print(f"No files modified in the last {args.days} days.")
        return
    for item in results[:args.limit]:
        print(f"{item['modified']}  {item['size']:>10}  {item['path']}")


def cmd_password(args):
    """Generate a random password."""
    print(generate_password(args.length))


def cmd_cleanup(args):
    """Clean up old files."""
    deleted = cleanup_old_files(args.directory, args.max_age)
    if not deleted:
        print("No files to clean up.")
        return
    print(f"Deleted {len(deleted)} file(s) older than {args.max_age} days:")
    for p in deleted:
        print(f"  {p}")


def main():
    parser = argparse.ArgumentParser(
        prog="toolbox",
        description="Personal toolbox - daily utility scripts and helpers",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p = subparsers.add_parser("system-info", help="Display system information")
    p.add_argument("--path", default=".", help="Path for disk usage")
    p.set_defaults(func=cmd_system_info)

    p = subparsers.add_parser("find-large", help="Find large files")
    p.add_argument("directory", default=".", nargs="?", help="Directory to scan")
    p.add_argument("--min-size", type=int, default=100, help="Min size in MB")
    p.set_defaults(func=cmd_find_large)

    p = subparsers.add_parser("duplicates", help="Find duplicate files")
    p.add_argument("directory", default=".", nargs="?", help="Directory to scan")
    p.set_defaults(func=cmd_duplicates)

    p = subparsers.add_parser("hash", help="Compute file hash")
    p.add_argument("files", nargs="+", help="File(s) to hash")
    p.add_argument("--algorithm", default="sha256", choices=["md5", "sha1", "sha256", "sha512"])
    p.set_defaults(func=cmd_hash)

    p = subparsers.add_parser("compress", help="Compress a file with gzip")
    p.add_argument("input", help="File to compress")
    p.add_argument("--output", default=None, help="Output path")
    p.set_defaults(func=cmd_compress)

    p = subparsers.add_parser("recent", help="Show recently modified files")
    p.add_argument("directory", default=".", nargs="?", help="Directory to scan")
    p.add_argument("--days", type=int, default=7, help="Lookback in days")
    p.add_argument("--limit", type=int, default=20, help="Max results")
    p.set_defaults(func=cmd_recent)

    p = subparsers.add_parser("password", help="Generate a random password")
    p.add_argument("--length", type=int, default=16, help="Password length")
    p.set_defaults(func=cmd_password)

    p = subparsers.add_parser("cleanup", help="Delete old files")
    p.add_argument("directory", help="Directory to clean")
    p.add_argument("--max-age", type=int, default=30, help="Max age in days")
    p.set_defaults(func=cmd_cleanup)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
