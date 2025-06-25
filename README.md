# Network Mapping and Scanning Tool

A Python-based tool for network scanning and enumeration that wraps common security tools like Nmap, Nikto, and WhatWeb.

## Features

- **Port Scanning**: Using Nmap for comprehensive port and service detection
- **Web Server Scanning**: Using Nikto to identify potential web vulnerabilities
- **Web Technology Detection**: Using WhatWeb to fingerprint web technologies
- **Parallel Execution**: Run multiple scans concurrently for efficiency
- **Structured Output**: Results saved in JSON format for easy processing
- **Logging**: Comprehensive logging for debugging and audit purposes

## Requirements

- Python 3.10+
- Kali Linux (or another Linux distribution with the required tools installed)
- The following tools must be installed and in your PATH:
  - nmap
  - nikto
  - whatweb

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd netmaptool
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```bash
python main.py <target> [options]
```

### Examples

1. Basic Nmap scan:
   ```bash
   python main.py example.com --tools nmap
   ```

2. Full scan with all tools:
   ```bash
   python main.py example.com --tools nmap nikto whatweb
   ```

3. Custom Nmap arguments:
   ```bash
   python main.py 192.168.1.1 --tools nmap --nmap-args "-sS -T4 -p 80,443,8080"
   ```

4. Specify output directory:
   ```bash
   python main.py example.com --output-dir ./scan_results
   ```

### Command Line Options

```
positional arguments:
  target                Target IP address or hostname to scan

optional arguments:
  -h, --help            show this help message and exit
  --tools TOOLS [TOOLS ...]
                        Tools to run (space-separated)
  --output-dir OUTPUT_DIR
                        Directory to save scan results
  --max-workers MAX_WORKERS
                        Maximum number of concurrent scans

Tool-specific options:
  --nmap-args NMAP_ARGS
                        Arguments for nmap: Port and service scanning with Nmap
  --nikto-args NIKTO_ARGS
                        Arguments for nikto: Web server scanning with Nikto
  --whatweb-args WHATWEB_ARGS
                        Arguments for whatweb: Web technology fingerprinting with WhatWeb
```

## Output

Scan results are saved in the specified output directory (default: `output/reports/`) with the following structure:

```
output/
└── reports/
    ├── nmap_results_<target>.json
    ├── nikto_results_<target>.json
    ├── whatweb_results_<target>.json
    └── combined_results_<target>.json
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
