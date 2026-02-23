# personal-toolbox

A collection of daily utility scripts and helpers for file management, system monitoring, text processing, and network tools.

## Quick Start

```bash
python3 toolbox.py --help
python3 toolbox.py <command> --help
```

## Commands

| Command | Description |
|---|---|
| `system-info` | Display system info (hostname, uptime, CPU, memory, disk) |
| `find-large` | Find files larger than a given size |
| `duplicates` | Find duplicate files by content hash |
| `hash` | Compute file checksum (md5, sha1, sha256, sha512) |
| `compress` | Compress a file with gzip |
| `recent` | List recently modified files |
| `password` | Generate a random password |
| `cleanup` | Delete files older than N days |

## Usage Examples

```bash
# System information
python3 toolbox.py system-info --path /

# Find files larger than 500MB
python3 toolbox.py find-large /home/user --min-size 500

# Find duplicate files
python3 toolbox.py duplicates /home/user/documents

# Compute SHA-256 hash
python3 toolbox.py hash myfile.zip --algorithm sha256

# Compress a file
python3 toolbox.py compress backup.tar --output backup.tar.gz

# Show files modified in the last 3 days (limit 10)
python3 toolbox.py recent . --days 3 --limit 10

# Generate a 24-character password
python3 toolbox.py password --length 24

# Clean up files older than 90 days
python3 toolbox.py cleanup /tmp/old-files --max-age 90
```

## Requirements

- Python 3.6+
- Linux (for `/proc`-based memory and uptime info)

No external dependencies required. Uses only the standard library.

## License

MIT
