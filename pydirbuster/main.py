import os
import argparse
import aiohttp
import asyncio
from datetime import datetime
import sys
import random
import json
import csv
import string
from urllib.parse import urlparse, urljoin

# Rich UI imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

console = Console()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]

WAF_SIGNATURES = {
    "cloudflare": ["cloudflare", "cf-ray", "cf-cache-status"],
    "akamai": ["akamai", "x-akamai"],
    "sucuri": ["x-sucuri-id", "x-sucuri-cache"],
    "aws": ["awselb", "x-amz-cf-id"],
    "imperva": ["incap_ses", "visid_incap"]
}

def print_banner():
    banner = r"""[bold red]
 ███████████             ██████████    ███            ███████████  █████  █████          █████                      
░░███░░░░░███           ░░███░░░░███  ░░░            ░░███░░░░░███░░███  ░░███          ░░███                       
 ░███    ░███ █████ ████ ░███   ░░███ ████  ████████  ░███    ░███ ░███   ░███   █████  ███████    ██████  ████████ 
 ░██████████ ░░███ ░███  ░███    ░███░░███ ░░███░░███ ░██████████  ░███   ░███  ███░░  ░░░███░    ███░░███░░███░░███
 ░███░░░░░░   ░███ ░███  ░███    ░███ ░███  ░███ ░░░  ░███░░░░░███ ░███   ░███ ░░█████   ░███    ░███████  ░███ ░░░ 
 ░███         ░███ ░███  ░███    ███  ░███  ░███      ░███    ░███ ░███   ░███  ░░░░███  ░███ ███░███░░░   ░███     
 █████        ░░███████  ██████████   █████ █████     ███████████  ░░████████   ██████   ░░█████ ░░██████  █████    
░░░░░          ░░░░░███ ░░░░░░░░░░   ░░░░░ ░░░░░     ░░░░░░░░░░░    ░░░░░░░░   ░░░░░░     ░░░░░   ░░░░░░  ░░░░░     
               ███ ░███                                                                                             
              ░░██████                                                                                              
               ░░░░░░                                                                                               [/bold red]
    """
    console.print(banner)
    author_info = "[bold white]PROFESSIONAL DIRECTORY BRUTE-FORCER[/bold white]\n[bold bright_red]By @hamzaatmacaa & @egnake (Ege Parlak)[/bold bright_red]"
    console.print(Panel(author_info, style="bold red", expand=False))

def parse_args(args_list=None):
    parser = argparse.ArgumentParser(description="PyDirBuster - Asynchronous Directory Brute-Forcer")
    parser.add_argument("-u", "--url", required=False, help="Target URL (e.g., https://example.com)")
    parser.add_argument("-w", "--wordlist", required=False, default="raft-large-directories.txt", help="Wordlist file path (e.g., wordlist.txt)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Number of concurrent asynchronous requests (default: 50)")
    parser.add_argument("-x", "--extensions", type=str, default="", help="Comma-separated extensions to add (e.g., php,txt)")
    
    # Advanced Filtering & Delay
    parser.add_argument("--exclude-status", type=str, default="404", help="Comma-separated status codes to exclude (default: 404)")
    parser.add_argument("--exclude-sizes", type=str, default="", help="Comma-separated response sizes to exclude")
    parser.add_argument("--exclude-words", type=str, default="", help="Comma-separated word counts to exclude")
    parser.add_argument("--delay", type=str, default="0", help="Delay between requests in seconds. Can be range (e.g., 0.1-1.0)")
    parser.add_argument("--smart-filter", action="store_true", default=True, help="Auto-detect Catch-All servers and filter them")
    
    # Evasion & Tampering
    parser.add_argument("--evade", action="store_true", help="Add X-Forwarded-For and Client-IP spoofing headers for WAF evasion")
    parser.add_argument("--tamper", action="store_true", help="Verb Tampering: Try POST/OPTIONS/PUT on 403 Forbidden endpoints")
    parser.add_argument("--pollute", action="store_true", help="Parameter Pollution: Append dummy parameters to bypass cache/rules")
    
    # Recursive Options
    parser.add_argument("-r", "--recursive", action="store_true", help="Enable recursive directory scanning")
    parser.add_argument("--depth", type=int, default=3, help="Maximum depth for recursive scanning (default: 3)")
    
    # Network
    parser.add_argument("--proxy", type=str, default="", help="Proxy URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("-H", "--header", action="append", default=[], help="Custom header (e.g., 'Authorization: Bearer xyz')")
    parser.add_argument("--no-random-agent", action="store_true", help="Disable random User-Agents")
    
    # Output & Resume
    parser.add_argument("-f", "--format", type=str, choices=["txt", "json", "csv"], default="txt", help="Output report format")
    parser.add_argument("-o", "--output", type=str, default="", help="Custom output file name")
    parser.add_argument("--resume", type=str, default="", help="Resume scan from a saved state file (.json)")
    
    return parser.parse_args(args_list)

def prepare_wordlist(wordlist_path, extensions_str):
    if not os.path.exists(wordlist_path):
        internal_path = os.path.join(os.path.dirname(__file__), "wordlists", wordlist_path)
        if os.path.exists(internal_path):
            wordlist_path = internal_path
        else:
            console.print(f"[bold red][-] Error: '{wordlist_path}' file not found locally or in package wordlists! Exiting.[/bold red]")
            sys.exit(1)

    words = []
    extensions = [ext.strip() for ext in extensions_str.split(",") if ext.strip()]
    
    with open(wordlist_path, "r", encoding="utf-8") as file:
        for line in file:
            word = line.strip()
            if not word:
                continue
            words.append(word)
            for ext in extensions:
                if ext.startswith('.'):
                    words.append(f"{word}{ext}")
                else:
                    words.append(f"{word}.{ext}")
                    
    return list(dict.fromkeys(words))

def write_finding(report_file, fmt, finding):
    with open(report_file, "a", encoding="utf-8", newline="") as report:
        if fmt == "txt":
            report.write(finding['log_text'] + "\n")
        elif fmt == "json":
            json.dump(finding, report)
            report.write("\n")
        elif fmt == "csv":
            writer = csv.writer(report)
            writer.writerow([finding['url'], finding['status'], finding['size'], finding['words'], finding['redirect']])
        report.flush()

async def check_waf(session, url):
    try:
        async with session.get(url, allow_redirects=False, timeout=5) as response:
            headers_str = str(response.headers).lower()
            for waf_name, signatures in WAF_SIGNATURES.items():
                for sig in signatures:
                    if sig in headers_str:
                        console.print(f"[bold red blink][!] WAF/CDN Detected: {waf_name.upper()} (Found signature: {sig})[/bold red blink]")
                        return waf_name
    except:
        pass
    return None

async def smart_calibration(session, url, exclude_sizes, exclude_words):
    console.print("[bold yellow][*] Performing Smart Calibration (Catch-All detection)...[/bold yellow]")
    random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    test_url = urljoin(url, random_path)
    try:
        async with session.get(test_url, allow_redirects=False, timeout=5) as response:
            if response.status == 200:
                content = await response.read()
                text = content.decode('utf-8', errors='ignore')
                size = len(content)
                words = len(text.split())
                console.print("[bold red][!] Catch-All Server Detected! (200 OK for random path)[/bold red]")
                console.print(f"[bold red][-] Auto-filtering Size: {size} bytes, Words: {words}[/bold red]")
                exclude_sizes.append(size)
                exclude_words.append(words)
            else:
                console.print("[bold green][+] Server looks normal (Not a Catch-All).[/bold green]")
    except:
        console.print("[bold yellow][-] Smart Calibration failed, continuing normally.[/bold yellow]")

def parse_delay(delay_str):
    if "-" in delay_str:
        min_d, max_d = delay_str.split("-")
        return float(min_d), float(max_d)
    return float(delay_str), float(delay_str)

def get_evasion_headers():
    fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    return {
        "X-Forwarded-For": fake_ip,
        "X-Originating-IP": fake_ip,
        "X-Remote-IP": fake_ip,
        "X-Remote-Addr": fake_ip,
        "Client-IP": fake_ip,
        "True-Client-IP": fake_ip
    }

async def tamper_verb(session, url, proxy):
    methods = ["POST", "OPTIONS", "PUT", "TRACE"]
    results = []
    for method in methods:
        try:
            async with session.request(method, url, allow_redirects=False, timeout=3, proxy=proxy) as response:
                if response.status != 403 and response.status != 404:
                    results.append(f"{method}:{response.status}")
        except:
            pass
    return results

async def scan_url(session, base_url, word, args, exclude_statuses, exclude_sizes, exclude_words, delay_min, delay_max, proxy):
    if delay_max > 0:
        await asyncio.sleep(random.uniform(delay_min, delay_max))

    if not base_url.endswith("/"):
        base_url += "/"
    
    # Parameter Pollution
    if args.pollute:
        pollution_string = f"?debug=true&admin=1&cache_bypass={''.join(random.choices(string.ascii_letters, k=5))}"
        test_url = urljoin(base_url, word) + pollution_string
    else:
        test_url = urljoin(base_url, word)
    
    headers = {}
    if not args.no_random_agent:
        headers['User-Agent'] = random.choice(USER_AGENTS)
    if args.evade:
        headers.update(get_evasion_headers())
    
    try:
        async with session.get(test_url, headers=headers, allow_redirects=False, timeout=5, proxy=proxy) as response:
            content = await response.read()
            text = content.decode('utf-8', errors='ignore')
            
            status = response.status
            content_size = len(content)
            word_count = len(text.split())
            
            if str(status) in exclude_statuses or content_size in exclude_sizes or word_count in exclude_words:
                return None
                
            redirect_target = response.headers.get('Location', '')
            tamper_info = ""
            
            # Verb Tampering Trigger
            if status == 403 and args.tamper:
                tamper_results = await tamper_verb(session, test_url, proxy)
                if tamper_results:
                    tamper_info = f" [Bypass: {', '.join(tamper_results)}]"
            
            log_text = ""
            ui_text = ""
            
            if status == 200:
                log_text = f"  200   | {content_size:<6} | {word_count:<5} | {test_url}"
                ui_text = f"[bold green][+][/bold green] {test_url} [green](200 OK)[/green] [dim]S:{content_size} W:{word_count}[/dim]"
            elif status == 403:
                log_text = f"  403   | {content_size:<6} | {word_count:<5} | {test_url}{tamper_info}"
                ui_text = f"[bold yellow]\\[/][/bold yellow] {test_url} [yellow](403 Forbidden)[/yellow] [dim]S:{content_size} W:{word_count}[/dim][bold magenta]{tamper_info}[/bold magenta]"
            elif status in [301, 302]:
                log_text = f"  {status}   | {content_size:<6} | {word_count:<5} | {test_url} -> {redirect_target}"
                ui_text = f"[bold blue][*][/bold blue] {test_url} [blue]({status} -> {redirect_target})[/blue]"
            else:
                log_text = f"  {status}   | {content_size:<6} | {word_count:<5} | {test_url}"
                ui_text = f"[bold magenta][?][/bold magenta] {test_url} [magenta]({status})[/magenta] [dim]S:{content_size}[/dim]"
                
            finding = {
                'url': test_url,
                'status': status,
                'size': content_size,
                'words': word_count,
                'redirect': redirect_target,
                'log_text': log_text,
                'ui_text': ui_text,
                'is_dir': ("." not in word)
            }
            return finding
    except Exception as e:
        # Silently drop failed connection attempts
        return None

def save_state(state_file, queue_list, scanned_dirs, current_dir_info):
    state = {
        "queue": queue_list,
        "scanned_dirs": list(scanned_dirs),
        "current_dir": current_dir_info
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f)

async def main_async(args):
    target_url = args.url
    if target_url and not target_url.startswith(("http://", "https://")):
        console.print(f"[bold red][*] No HTTP schema provided. Defaulting to https://{target_url}[/bold red]")
        target_url = "https://" + target_url
        
    if not target_url.endswith("/"):
        target_url += "/"
        
    words = prepare_wordlist(args.wordlist, args.extensions)
    
    # Headers Setup
    custom_headers = {}
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            custom_headers[k.strip()] = v.strip()
    
    if args.no_random_agent:
        custom_headers['User-Agent'] = USER_AGENTS[0]
        
    # Output Setup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fmt = args.format
    report_file = args.output if args.output else f"scan_report_{timestamp}.{fmt}"
    state_file = f"resume_state.json"
    
    # Build Config Table using Rich
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="bold red")
    table.add_column("Value", style="bold white")
    table.add_row("Target URL", target_url)
    table.add_row("Wordlist Size", f"{len(words)} payloads")
    table.add_row("Concurrency", f"{args.threads} async tasks")
    if args.delay != "0": table.add_row("Delay/Stealth", f"{args.delay}s")
    if args.recursive: table.add_row("Recursive", f"Enabled (Depth: {args.depth})")
    if args.evade: table.add_row("Header Evasion", "[bright_red]Active (Spoofing IP)[/bright_red]")
    if args.tamper: table.add_row("Verb Tampering", "[bright_red]Active (Testing 403s)[/bright_red]")
    if args.pollute: table.add_row("Param Pollution", "[bright_red]Active (?debug=true...)[/bright_red]")
    if args.proxy: table.add_row("Proxy", args.proxy)
    table.add_row("Report Format", fmt.upper())
    table.add_row("Report File", report_file)
    
    console.print(Panel(table, title="[bold white]Scan Configuration[/bold white]", expand=False, border_style="red"))

    # Initial Report Write
    with open(report_file, "a", encoding="utf-8", newline="") as report:
        if fmt == "txt":
            report.write(f"=======================================================================\n")
            report.write(f"                     PYDIRBUSTER - SECURITY AUDIT REPORT               \n")
            report.write(f"=======================================================================\n")
            report.write(f"[+] Target URL      : {target_url}\n")
            report.write(f"[+] Scan Start Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report.write(f"[+] Concurrency     : {args.threads} Threads\n")
            report.write(f"[+] Wordlist Size   : {len(words)} payloads\n")
            
            evasion_flags = []
            if args.evade: evasion_flags.append("IP Spoofing")
            if args.tamper: evasion_flags.append("Verb Tampering")
            if args.pollute: evasion_flags.append("Parameter Pollution")
            if args.delay != "0": evasion_flags.append(f"Rate Limit ({args.delay}s)")
            
            if evasion_flags:
                report.write(f"[+] Evasion Tactics : {', '.join(evasion_flags)}\n")
            else:
                report.write(f"[+] Evasion Tactics : None (Noisy Scan)\n")
                
            report.write(f"=======================================================================\n")
            report.write(f" STATUS |  SIZE  | WORDS | URL\n")
            report.write(f"-----------------------------------------------------------------------\n")
        elif fmt == "csv":
            writer = csv.writer(report)
            writer.writerow(["URL", "Status Code", "Size", "Word Count", "Redirect Location"])

    exclude_statuses = [s.strip() for s in args.exclude_status.split(",") if s.strip()]
    exclude_sizes = [int(s.strip()) for s in args.exclude_sizes.split(",") if s.strip()]
    exclude_words = [int(s.strip()) for s in args.exclude_words.split(",") if s.strip()]
    delay_min, delay_max = parse_delay(args.delay)
    
    proxy = args.proxy if args.proxy else None

    # Initialize aiohttp Session
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector, headers=custom_headers) as session:
        # 1. WAF Check
        await check_waf(session, target_url)
        
        # 2. Smart Calibration
        if args.smart_filter:
            await smart_calibration(session, target_url, exclude_sizes, exclude_words)
            
        console.print("[bold red]\n[*] Initializing scan engines...[/bold red]")

        # 3. Setup Queue and Resume logic
        dirs_to_scan = []
        scanned_dirs = set()
        
        if args.resume and os.path.exists(args.resume):
            console.print(f"[bold red][*] Resuming from state file: {args.resume}[/bold red]")
            with open(args.resume, "r", encoding="utf-8") as f:
                state = json.load(f)
                dirs_to_scan = state.get("queue", [])
                scanned_dirs = set(state.get("scanned_dirs", []))
                if state.get("current_dir"):
                    dirs_to_scan.insert(0, state["current_dir"])
        else:
            dirs_to_scan.append({"url": target_url, "depth": 0})
            
        try:
            while dirs_to_scan:
                current_dir_info = dirs_to_scan.pop(0)
                current_url = current_dir_info["url"]
                current_depth = current_dir_info["depth"]
                
                if current_url in scanned_dirs:
                    continue
                    
                scanned_dirs.add(current_url)
                
                if current_depth > 0:
                    console.print(f"\n[bold red][*] Recursion Triggered: Scanning {current_url} (Depth: {current_depth})[/bold red]")

                sem = asyncio.Semaphore(args.threads)
                
                async def bounded_scan(w):
                    async with sem:
                        return await scan_url(session, current_url, w, args, exclude_statuses, exclude_sizes, exclude_words, delay_min, delay_max, proxy)
                
                tasks = [bounded_scan(w) for w in words]
                
                # Rich Progress Bar setup
                with Progress(
                    SpinnerColumn(style="bold red"),
                    TextColumn("[bold white]{task.description}"),
                    BarColumn(complete_style="red", finished_style="bold red"),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    console=console,
                    transient=True # Disappears when done
                ) as progress:
                    
                    task_id = progress.add_task(f"Scanning {urlparse(current_url).path or '/'}", total=len(tasks))
                    
                    for f in asyncio.as_completed(tasks):
                        finding = await f
                        if finding:
                            console.print(finding['ui_text'])
                            write_finding(report_file, fmt, finding)
                            
                            if args.recursive and current_depth < args.depth and finding['is_dir']:
                                new_dir_url = finding['url']
                                if not new_dir_url.endswith("/"):
                                    new_dir_url += "/"
                                dirs_to_scan.append({"url": new_dir_url, "depth": current_depth + 1})
                                
                        progress.update(task_id, advance=1)
                        
                save_state(state_file, dirs_to_scan, scanned_dirs, None)
                
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            raise

    console.print(f"\n[bold red]=== Scanning Task Completed ===[/bold red]")
    console.print(f"[bold red][+] Checked {len(scanned_dirs)} unique directories.[/bold red]")
    console.print(f"[bold red][+] Check your final report here: {report_file}[/bold red]")
    
    if os.path.exists(state_file):
        os.remove(state_file)

def main():
    print_banner()
    
    if len(sys.argv) == 1:
        import shlex
        console.print("[bold yellow][*] Interactive Mode: Enter arguments as you would in the command line.[/bold yellow]")
        console.print("[dim]    Example: -u https://example.com -w wordlist.txt -t 100 --evade --tamper\n[/dim]")
        while True:
            try:
                user_input = console.input("[bold green]pydirbuster > [/bold green]")
                args_list = shlex.split(user_input)
                args = parse_args(args_list)
                if not args.url and not args.resume:
                    console.print("[bold red][-] Error: Either -u/--url or --resume must be provided.[/bold red]")
                    continue
                if not args.wordlist and not args.resume:
                    console.print("[bold red][-] Error: -w/--wordlist must be provided.[/bold red]")
                    continue
                break
            except KeyboardInterrupt:
                console.print("\n[bold red][-] Exiting...[/bold red]")
                sys.exit(0)
            except SystemExit:
                console.print("[bold red][-] Invalid arguments. Try again.\n[/bold red]")
    else:
        args = parse_args()
        if not args.url and not args.resume:
            console.print("[bold red][-] Error: Either -u/--url or --resume must be provided.[/bold red]")
            sys.exit(1)
        if not args.wordlist and not args.resume:
            console.print("[bold red][-] Error: -w/--wordlist must be provided.[/bold red]")
            sys.exit(1)

    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(main_async(args))
        
    except KeyboardInterrupt:
        console.print(f"\n\n[bold red][-] Scan interrupted by user. State saved to 'resume_state.json'.[/bold red]")
        console.print(f"[bold red][-] You can resume later using: pydirbuster --resume resume_state.json -w wordlist.txt[/bold red]")
        sys.exit(0)

if __name__ == "__main__":
    main()
