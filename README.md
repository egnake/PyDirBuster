# PyDirBuster

A high-performance, highly-evasive asynchronous directory brute-forcing tool written in Python. Powered by `aiohttp` and `asyncio`, PyDirBuster is capable of firing thousands of concurrent requests per second while maintaining a stealthy profile.

PyDirBuster features advanced Web Application Firewall (WAF) evasion, HTTP Verb Tampering, Parameter Pollution, and a modern terminal UI. It is fully installable via `pip`.

## Authors & Acknowledgements
* [egnake (Ege Parlak)](https://github.com/egnake/PyDirBuster) - Asynchronous engine, Evasion tactics, and UI implementation.
* [hamzaatmacaa](https://github.com/hamzaatmacaa/PyDirBuster) - Original foundational logic and structure.
* The default wordlist provided is from [Daniel Miessler's SecLists](https://github.com/danielmiessler/SecLists/tree/master/Discovery/Web-Content).

---

## Features & Evasion Tactics

* **High Performance:** Utilizes Python's `asyncio` for non-blocking I/O operations and asynchronous HTTP requests.
* **WAF Evasion (`--evade`):** Spoofs `X-Forwarded-For` and `Client-IP` headers to manipulate WAF rules and masquerade as internal networks or trusted sources.
* **HTTP Verb Tampering (`--tamper`):** Automatically attacks `403 Forbidden` directories by switching request methods to `POST`, `OPTIONS`, `PUT`, and `TRACE` to bypass poorly configured Access Control Lists (ACLs).
* **Parameter Pollution (`--pollute`):** Appends random, dummy query parameters (e.g., `?debug=true&admin=1`) to bypass aggressive caching and exact-match WAF rules.
* **Smart Calibration (Auto-Tune):** Automatically detects "Catch-All" server behavior before scanning begins and filters false positives based on response sizes and word counts.
* **Modern Terminal UI:** Features configuration tables, dynamic progress bars, and color-coded logging using the `rich` library.
* **State Resumption (`--resume`):** Allows scans to be paused and resumed seamlessly from a saved state file without losing progress.
* **Recursive Scanning (`--recursive`):** Discovers hidden directory structures down to a configurable depth.

---

## Installation

PyDirBuster can be installed globally as a CLI package.

1. Clone the repository:
   ```bash
   git clone https://github.com/egnake/PyDirBuster.git
   cd PyDirBuster
   ```

2. Install globally via `pip`:
   ```bash
   pip install .
   ```

3. Execute from anywhere:
   ```bash
   pydirbuster -h
   ```

### Uninstallation

To completely remove PyDirBuster from your system:

```bash
pip uninstall pydirbuster
```

---

## Usage Examples

**1. The Evasion Scan:**
*(Spoofs IPs, Tampers Verbs, Pollutes Parameters, Randomizes Agents, Bypasses Catch-Alls)*
```bash
pydirbuster -u https://example.com -w raft-large-directories.txt -t 50 --evade --tamper --pollute
```

**2. Fast Recursive Scan (JSON Output):**
```bash
pydirbuster -u https://example.com -w raft-large-directories.txt -t 200 -r --depth 3 -f json
```

**3. Stealth Mode (Randomized Rate Limiting):**
```bash
pydirbuster -u https://example.com -w raft-large-directories.txt --delay 0.1-1.5
```

---

## Available Arguments

| Argument | Description |
| :--- | :--- |
| `-u`, `--url` | Target URL (e.g., https://example.com) |
| `-w`, `--wordlist` | Path to the wordlist file |
| `-t`, `--threads` | Number of concurrent asynchronous requests (default: 50) |
| `-x`, `--extensions` | Comma-separated file extensions to append (e.g., `php,txt`) |
| `--evade` | Add X-Forwarded-For and Client-IP spoofing headers |
| `--tamper` | Verb Tampering: Test POST/OPTIONS/PUT/TRACE on 403 endpoints |
| `--pollute` | Parameter Pollution: Append dummy cache-busting parameters |
| `--exclude-status` | Comma-separated HTTP status codes to ignore |
| `--exclude-sizes` | Comma-separated response sizes (in bytes) to ignore |
| `--smart-filter` | Enable automatic Catch-All detection and filtering |
| `--delay` | Delay between requests (e.g., `0.5` or range `0.1-1.5`) |
| `-r`, `--recursive` | Enable recursive directory scanning |
| `--depth` | Maximum recursion depth (default: 3) |
| `--proxy` | Proxy URL (e.g., `http://127.0.0.1:8080`) |
| `-H`, `--header` | Custom HTTP headers (`-H "Cookie: session=1"`) |
| `-f`, `--format` | Output report format (`txt`, `json`, `csv`) |
| `--resume` | Resume scan from a specific state file (`resume_state.json`) |

---

## License
This project is licensed under the [MIT License](LICENSE).

## Disclaimer
This tool is developed strictly for educational purposes, security awareness, and ethical penetration testing. Do not execute this script against any infrastructure or server without explicit, written permission from the target owner. The authors accept no liability for any unauthorized actions, misuse, or damage caused by this utility.
